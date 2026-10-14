import math
from dataclasses import asdict, dataclass

TICK = 0.05


def round_tick(price: float) -> float:
    return round(round(price / TICK) * TICK, 2)


@dataclass
class TradePlan:
    symbol: str
    security_id: str
    qty: int
    entry_limit: float
    stop_loss: float
    target: float
    final_score: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_plan(candidates: list[dict], reviews: dict[str, dict], market: dict, *,
               capital_per_trade: float, max_positions: int, available_funds: float,
               stop_loss_pct: float, target_pct: float) -> tuple[list[TradePlan], list[str]]:
    """Merge screener + agent output into sized orders. Agents can only remove trades, never add or resize them."""
    notes: list[str] = []
    if not market.get("allow_new_positions", False):
        return [], ["Market-context agent blocked new positions: " + "; ".join(market.get("reasons", []))]

    ranked = []
    for c in candidates:
        review = reviews.get(c["symbol"])
        if review is None:
            notes.append(f"{c['symbol']}: no catalyst review, skipped")
            continue
        if review["veto"]:
            notes.append(f"{c['symbol']}: vetoed ({'; '.join(review['red_flags']) or review['summary']})")
            continue
        catalyst = max(-2, min(2, int(review["catalyst_score"])))
        if catalyst < 0:
            notes.append(f"{c['symbol']}: negative catalyst, skipped")
            continue
        ranked.append((c["score"] + 10 * catalyst, c, review))
    ranked.sort(key=lambda r: r[0], reverse=True)

    plans: list[TradePlan] = []
    funds = available_funds
    for final_score, c, review in ranked[:max_positions]:
        entry = round_tick(c["ltp"] * 1.002)
        budget = min(capital_per_trade, funds)
        qty = math.floor(budget / entry)
        if qty < 1:
            notes.append(f"{c['symbol']}: insufficient funds for 1 share")
            continue
        funds -= qty * entry
        plans.append(TradePlan(
            symbol=c["symbol"], security_id=c["security_id"], qty=qty, entry_limit=entry,
            stop_loss=round_tick(entry * (1 - stop_loss_pct / 100)),
            target=round_tick(entry * (1 + target_pct / 100)),
            final_score=round(final_score, 1), reason=review["summary"],
        ))
    return plans, notes


@dataclass
class SellIdea:
    symbol: str
    security_id: str
    entry_limit: float
    stop_loss: float
    target: float
    final_score: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_sell_ideas(losers: list[dict], reviews: dict[str, dict], *, max_ideas: int,
                     stop_loss_pct: float, target_pct: float) -> tuple[list[SellIdea], list[str]]:
    """Sell (short) ideas from the day's biggest losers. Advisory only: a cash BTST trade is long-only, so these
    are intraday or stock-futures trades the tool never places. The review rules are the mirror of the buy side:
    event risk (results due, ban list, surveillance) still vetoes, bad news helps, good news is squeeze risk."""
    notes: list[str] = []
    ranked = []
    for c in losers:
        review = reviews.get(c["symbol"])
        if review is None:
            notes.append(f"{c['symbol']}: no review, skipped")
            continue
        if review["veto"]:
            notes.append(f"{c['symbol']}: sell idea vetoed ({'; '.join(review['red_flags']) or review['summary']})")
            continue
        catalyst = max(-2, min(2, int(review["catalyst_score"])))
        if catalyst > 0:
            notes.append(f"{c['symbol']}: positive news, short-squeeze risk, skipped")
            continue
        ranked.append((c.get("weak_score", 0) - 10 * catalyst, c, review))
    ranked.sort(key=lambda r: r[0], reverse=True)

    ideas = []
    for score, c, review in ranked[:max_ideas]:
        entry = round_tick(c["ltp"] * 0.998)
        ideas.append(SellIdea(
            symbol=c["symbol"], security_id=c["security_id"], entry_limit=entry,
            stop_loss=round_tick(entry * (1 + stop_loss_pct / 100)),
            target=round_tick(entry * (1 - target_pct / 100)),
            final_score=round(score, 1), reason=review["summary"],
        ))
    return ideas, notes
