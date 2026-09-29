import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dhanhq import DhanContext, dhanhq

log = logging.getLogger(__name__)

SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"


class DhanError(RuntimeError):
    pass


def _unwrap(resp: dict):
    if resp.get("status") != "success":
        raise DhanError(resp.get("remarks"))
    return resp["data"]


class Dhan:
    def __init__(self, client_id: str, access_token: str, data_dir: Path):
        if not client_id or not access_token:
            raise DhanError("Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env")
        self.api = dhanhq(DhanContext(client_id, access_token))
        self.data_dir = data_dir

    def security_ids(self, symbols: list[str]) -> dict[str, str]:
        """Map NSE equity trading symbols to Dhan security IDs (scrip master cached per day)."""
        cache = self.data_dir / f"scrip-master-{date.today()}.csv"
        if not cache.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            pd.read_csv(SCRIP_MASTER_URL, low_memory=False).to_csv(cache, index=False)
        df = pd.read_csv(cache, low_memory=False)
        eq = df[(df["SEM_EXM_EXCH_ID"] == "NSE") & (df["SEM_SEGMENT"] == "E") & (df["SEM_SERIES"] == "EQ")]
        mapping = dict(zip(eq["SEM_TRADING_SYMBOL"].str.replace(r"-EQ$", "", regex=True),
                           eq["SEM_SMST_SECURITY_ID"].astype(str)))
        missing = [s for s in symbols if s not in mapping]
        if missing:
            log.warning("Not found in NSE EQ series (skipped): %s", ", ".join(missing))
        return {s: mapping[s] for s in symbols if s in mapping}

    def daily_history(self, security_id: str, days: int = 120) -> pd.DataFrame:
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        data = _unwrap(self.api.historical_daily_data(
            security_id, "NSE_EQ", "EQUITY", from_date.isoformat(), to_date.isoformat()))
        df = pd.DataFrame({k: data[k] for k in ("open", "high", "low", "close", "volume")})
        df["date"] = pd.to_datetime(data["timestamp"], unit="s", utc=True).tz_convert("Asia/Kolkata").date
        return df

    def quotes(self, security_ids: list[str]) -> dict[str, dict]:
        """Full quotes (LTP, today's OHLC, volume, circuit limits) keyed by security ID."""
        out: dict[str, dict] = {}
        for i in range(0, len(security_ids), 1000):
            chunk = [int(s) for s in security_ids[i:i + 1000]]
            data = _unwrap(self.api.quote_data({"NSE_EQ": chunk}))
            out.update({str(k): v for k, v in data["data"]["NSE_EQ"].items()})
            time.sleep(1)
        return out

    def index_snapshot(self) -> dict:
        """Nifty 50 (13), Bank Nifty (25) and India VIX (21) from Dhan's IDX_I segment."""
        names = {"13": "NIFTY 50", "25": "NIFTY BANK", "21": "INDIA VIX"}
        data = _unwrap(self.api.ohlc_data({"IDX_I": [13, 25, 21]}))
        return {names.get(str(k), str(k)): v for k, v in data["data"]["IDX_I"].items()}

    def ltp(self, security_ids: list[str]) -> dict[str, float]:
        data = _unwrap(self.api.ticker_data({"NSE_EQ": [int(s) for s in security_ids]}))
        return {str(k): float(v["last_price"]) for k, v in data["data"]["NSE_EQ"].items()}

    def available_funds(self) -> float:
        data = _unwrap(self.api.get_fund_limits())
        return float(data.get("availabelBalance", data.get("availableBalance", 0)))

    def place_order(self, security_id: str, side: str, qty: int, price: float | None, tag: str) -> str:
        order_type = dhanhq.LIMIT if price else dhanhq.MARKET
        data = _unwrap(self.api.place_order(
            security_id=security_id,
            exchange_segment=dhanhq.NSE,
            transaction_type=side,
            quantity=qty,
            order_type=order_type,
            product_type=dhanhq.CNC,
            price=price or 0,
            tag=tag,
        ))
        return str(data["orderId"])

    def order_status(self, order_id: str) -> dict:
        return _unwrap(self.api.get_order_by_id(order_id))
