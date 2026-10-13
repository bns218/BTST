from dataclasses import asdict, dataclass
from datetime import date

import pandas as pd


@dataclass
class Candidate:
    symbol: str
    security_id: str
    ltp: float
    day_change_pct: float
    close_position: float
    volume_ratio: float
    rsi14: float
    above_ema20: bool
    above_ema50: bool
    breakout_20d: bool
    turnover_cr: float
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    last_loss = loss.iloc[-1]
    if last_loss == 0:
        return 100.0
    return float(100 - 100 / (1 + gain.iloc[-1] / last_loss))


def with_today(history: pd.DataFrame, quote: dict, today: date) -> pd.DataFrame:
    """Append (or replace) today's in-progress candle built from a live Dhan quote."""
    ohlc = quote["ohlc"]
    row = {
        "open": float(ohlc["open"]), "high": float(ohlc["high"]), "low": float(ohlc["low"]),
        "close": float(quote["last_price"]), "volume": float(quote["volume"]), "date": today,
    }
    past = history[history["date"] != today]
    return pd.concat([past, pd.DataFrame([row])], ignore_index=True)


def evaluate(symbol: str, security_id: str, df: pd.DataFrame, quote: dict,
             min_turnover_cr: float) -> Candidate | None:
    """Score one stock for BTST. `df` must end with today's candle. Returns None if it fails hard filters."""
    if len(df) < 55:
        return None
    today, prev = df.iloc[-1], df.iloc[-2]
    past20 = df.iloc[-21:-1]

    day_range = today["high"] - today["low"]
    close_position = (today["close"] - today["low"]) / day_range if day_range > 0 else 0.0
    day_change_pct = (today["close"] / prev["close"] - 1) * 100
    avg_vol = past20["volume"].mean()
    volume_ratio = today["volume"] / avg_vol if avg_vol > 0 else 0.0
    turnover_cr = float((past20["close"] * past20["volume"]).mean() / 1e7)
    ema20 = df["close"].ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
    rsi14 = _rsi(df["close"])
    breakout = today["close"] >= past20["high"].max()

    upper_circuit = float(quote.get("upper_circuit_limit") or 0)
    near_upper_circuit = upper_circuit > 0 and today["close"] >= upper_circuit * 0.99

    if (turnover_cr < min_turnover_cr or near_upper_circuit
            or not 0.5 <= day_change_pct <= 7 or close_position < 0.7 or volume_ratio < 1.2):
        return None

    score = (
        30 * close_position
        + 20 * min(volume_ratio / 3, 1)
        + 15 * (today["close"] > ema20)
        + 10 * (today["close"] > ema50)
        + 15 * breakout
        + 10 * (55 <= rsi14 <= 72)
    )
    return Candidate(
        symbol=symbol, security_id=security_id, ltp=round(float(today["close"]), 2),
        day_change_pct=round(float(day_change_pct), 2), close_position=round(float(close_position), 2),
        volume_ratio=round(float(volume_ratio), 2), rsi14=round(rsi14, 1),
        above_ema20=bool(today["close"] > ema20), above_ema50=bool(today["close"] > ema50),
        breakout_20d=bool(breakout), turnover_cr=round(turnover_cr, 1), score=round(float(score), 1),
    )


def mover_row(symbol: str, security_id: str, quote: dict, min_turnover_cr: float) -> dict | None:
    """One F&O stock's move today from a live quote. None if illiquid, unpriced, or pinned at a circuit limit."""
    ltp, prev = float(quote.get("last_price") or 0), float(quote["ohlc"]["close"] or 0)
    if ltp <= 0 or prev <= 0:
        return None
    high, low = float(quote["ohlc"]["high"]), float(quote["ohlc"]["low"])
    turnover_cr = float(quote.get("volume") or 0) * ltp / 1e7
    upper, lower = float(quote.get("upper_circuit_limit") or 0), float(quote.get("lower_circuit_limit") or 0)
    if turnover_cr < min_turnover_cr or (upper and ltp >= upper * 0.99) or (lower and ltp <= lower * 1.01):
        return None
    buy, sell = quote.get("buy_quantity"), quote.get("sell_quantity")
    change = (ltp / prev - 1) * 100
    pos = (ltp - low) / (high - low) if high > low else 0.5
    return {
        "symbol": symbol, "security_id": security_id, "ltp": round(ltp, 2), "day_change_pct": round(change, 2),
        "close_position": round(pos, 2), "turnover_cr": round(turnover_cr, 1),
        "sell_to_buy": round(float(sell) / float(buy), 2) if buy and sell else None,
        "score": round(40 * min(max(change, 0) / 5, 1) + 40 * pos + 20 * min(turnover_cr / 200, 1), 1),
    }


def rank_movers(rows: list[dict], n: int = 20) -> tuple[list[dict], list[dict]]:
    """Top n gainers (biggest rise first) and top n losers (biggest fall first)."""
    gainers = sorted((r for r in rows if r["day_change_pct"] > 0), key=lambda r: -r["day_change_pct"])[:n]
    losers = sorted((r for r in rows if r["day_change_pct"] < 0), key=lambda r: r["day_change_pct"])[:n]
    return gainers, losers
