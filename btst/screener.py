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
