import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .events import next_trading_day

PICK_FIELDS = ["date", "session", "side", "symbol", "ref_price", "stop", "target", "tags", "reason"]
RESULT_FIELDS = ["date", "session", "side", "symbol", "eval_date", "ref_price", "open_pct", "high_pct",
                 "low_pct", "close_pct", "move_pct", "correct", "outcome", "tags"]


@dataclass(frozen=True)
class Pick:
    day: date
    session: str          # "am" morning-brief watchlist (judged on the same day's close) or "pm" 3:05 list (judged on the next open)
    side: str             # "buy" or "sell"
    symbol: str
    ref_price: float      # am: previous close; pm: the price when the pick was made
    stop: float | None = None
    target: float | None = None
    tags: str = ""        # "|"-separated rationale tags, e.g. "news|sector"
    reason: str = ""

    def __post_init__(self):
        if self.session not in ("am", "pm") or self.side not in ("buy", "sell") or self.ref_price <= 0:
            raise ValueError(f"bad pick: {self}")

    @property
    def key(self) -> tuple:
        return (self.day.isoformat(), self.session, self.side, self.symbol)


def eval_day(pick: Pick, holidays: frozenset[date] = frozenset()) -> date:
    return pick.day if pick.session == "am" else next_trading_day(pick.day, holidays)


def score_pick(pick: Pick, bar: dict) -> dict:
    """Compare one pick with the real day bar {open, high, low, close}. Daily bars cannot say whether the
    target or the stop was touched first, so a bar that touches both is reported as 'ambiguous'."""
    ref, buy = pick.ref_price, pick.side == "buy"
    stop = pick.stop or ref * (0.99 if buy else 1.01)
    target = pick.target or ref * (1.02 if buy else 0.98)
    o, h, l, c = (float(bar[k]) for k in ("open", "high", "low", "close"))
    pct = lambda v: round((v / ref - 1) * 100, 2)
    move = pct(o) if pick.session == "pm" else pct(c)
    correct = move > 0 if buy else move < 0
    hit_t, hit_s = (h >= target, l <= stop) if buy else (l <= target, h >= stop)
    gap_s, gap_t = (o <= stop, o >= target) if buy else (o >= stop, o <= target)
    outcome = ("gap_through_stop" if gap_s else "gap_through_target" if gap_t else
               "ambiguous" if hit_t and hit_s else "target" if hit_t else "stop" if hit_s else "none")
    return {"open_pct": pct(o), "high_pct": pct(h), "low_pct": pct(l), "close_pct": pct(c),
            "move_pct": move, "correct": correct, "outcome": outcome}


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_picks(path: Path) -> list[Pick]:
    return [Pick(date.fromisoformat(r["date"]), r["session"], r["side"], r["symbol"], float(r["ref_price"]),
                 float(r["stop"]) if r["stop"] else None, float(r["target"]) if r["target"] else None,
                 r["tags"], r["reason"]) for r in _read(path)]


def add_picks(path: Path, picks: list[Pick]) -> int:
    rows = {(r["date"], r["session"], r["side"], r["symbol"]): r for r in _read(path)}
    added = 0
    for p in picks:
        added += p.key not in rows
        rows[p.key] = {"date": p.day.isoformat(), "session": p.session, "side": p.side, "symbol": p.symbol,
                       "ref_price": p.ref_price, "stop": p.stop or "", "target": p.target or "",
                       "tags": p.tags, "reason": p.reason}
    _write(path, PICK_FIELDS, list(rows.values()))
    return added


def pending(picks_path: Path, results_path: Path, today: date,
            holidays: frozenset[date] = frozenset()) -> list[tuple[Pick, date]]:
    done = {(r["date"], r["session"], r["side"], r["symbol"]) for r in _read(results_path)}
    out = [(p, eval_day(p, holidays)) for p in load_picks(picks_path) if p.key not in done]
    return sorted([x for x in out if x[1] <= today], key=lambda x: (x[1], x[0].symbol))


def score_pending(picks_path: Path, results_path: Path, bars: dict, today: date,
                  holidays: frozenset[date] = frozenset()) -> tuple[int, list[str]]:
    """`bars` is {"YYYY-MM-DD": {"SYMBOL": {open, high, low, close}}}. Returns (newly scored, missing 'DATE SYMBOL')."""
    rows = _read(results_path)
    scored, missing = 0, []
    for pick, day in pending(picks_path, results_path, today, holidays):
        bar = (bars.get(day.isoformat()) or {}).get(pick.symbol)
        if not bar:
            missing.append(f"{day.isoformat()} {pick.symbol}")
            continue
        rows.append({"date": pick.day.isoformat(), "session": pick.session, "side": pick.side, "symbol": pick.symbol,
                     "eval_date": day.isoformat(), "ref_price": pick.ref_price, "tags": pick.tags,
                     **score_pick(pick, bar)})
        scored += 1
    _write(results_path, RESULT_FIELDS, rows)
    return scored, missing


def summarize(results_path: Path, since: date | None = None) -> dict:
    rows = [r for r in _read(results_path) if since is None or date.fromisoformat(r["date"]) >= since]
    def agg(sel):
        n = len(sel); ok = sum(r["correct"] == "True" for r in sel)
        edge = [float(r["move_pct"]) * (1 if r["side"] == "buy" else -1) for r in sel]   # move in the picked direction
        return {"n": n, "correct": ok, "rate": round(100 * ok / n) if n else None,
                "avg_edge_pct": round(sum(edge) / n, 2) if n else None}
    groups: dict[str, dict] = {}
    for key in sorted({f"{r['session']}/{r['side']}" for r in rows}):
        groups[key] = agg([r for r in rows if f"{r['session']}/{r['side']}" == key])
    tags: dict[str, dict] = {}
    for tag in sorted({t for r in rows for t in r["tags"].split("|") if t}):
        tags[tag] = agg([r for r in rows if tag in r["tags"].split("|")])
    outcomes: dict[str, int] = {}
    for r in rows:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    days = sorted({r["date"] for r in rows})
    return {"overall": agg(rows), "by_group": groups, "by_tag": tags, "outcomes": outcomes,
            "days": len(days), "first": days[0] if days else None, "last": days[-1] if days else None}


def format_summary(s: dict) -> str:
    if not s["overall"]["n"]:
        return "No scored picks yet."
    o = s["overall"]
    lines = [f"{s['days']} days ({s['first']} to {s['last']}): {o['correct']}/{o['n']} picks moved the right way "
             f"({o['rate']}%), average edge {o['avg_edge_pct']:+.2f}% (move in the picked direction)", "", "By list:"]
    for k, g in s["by_group"].items():
        lines.append(f"  {k:<9} {g['correct']}/{g['n']} right ({g['rate']}%), avg edge {g['avg_edge_pct']:+.2f}%")
    if s["by_tag"]:
        lines += ["", "By reason tag:"]
        for k, g in s["by_tag"].items():
            lines.append(f"  {k:<14} {g['correct']}/{g['n']} right ({g['rate']}%), avg edge {g['avg_edge_pct']:+.2f}%")
    lines += ["", "Levels: " + ", ".join(f"{k} {v}" for k, v in sorted(s["outcomes"].items()))]
    return "\n".join(lines)


def load_bars(path: str) -> dict:
    return json.loads(Path(path).read_text())
