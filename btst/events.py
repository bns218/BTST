import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

FIELDS = ["symbol", "type", "date", "note", "source"]
BLOCKING_TYPES = {"results", "board_meeting"}
DEAL_TYPES = {"bulk_deal", "block_deal"}
TYPES = BLOCKING_TYPES | DEAL_TYPES | {"ex_date", "other"}


@dataclass(frozen=True)
class Event:
    symbol: str
    type: str
    date: date
    note: str = ""
    source: str = ""

    def __post_init__(self):
        if self.type not in TYPES:
            raise ValueError(f"unknown event type {self.type!r}; use one of {sorted(TYPES)}")


def next_trading_day(day: date, holidays: frozenset[date] = frozenset()) -> date:
    nxt = day + timedelta(days=1)
    while nxt.weekday() >= 5 or nxt in holidays:
        nxt += timedelta(days=1)
    return nxt


def load_holidays(path: Path) -> frozenset[date]:
    if not path.exists():
        return frozenset()
    return frozenset(date.fromisoformat(s.strip()) for s in path.read_text().splitlines()
                     if s.strip() and not s.startswith("#"))


class EventCalendar:
    def __init__(self, path: Path, holidays: frozenset[date] = frozenset()):
        self.path = path
        self.holidays = holidays
        self.events: dict[tuple[str, str, date], Event] = {}
        if path.exists():
            with path.open(newline="") as f:
                for row in csv.DictReader(f):
                    self.add(Event(row["symbol"], row["type"], date.fromisoformat(row["date"]),
                                   row.get("note", ""), row.get("source", "")))

    def add(self, event: Event) -> None:
        symbol = event.symbol.strip().upper()
        event = Event(symbol, event.type, event.date, event.note, event.source)
        self.events[(symbol, event.type, event.date)] = event

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for e in sorted(self.events.values(), key=lambda e: (e.date, e.symbol, e.type)):
                writer.writerow({"symbol": e.symbol, "type": e.type, "date": e.date.isoformat(),
                                 "note": e.note, "source": e.source})

    def between(self, start: date, end: date, symbol: str | None = None) -> list[Event]:
        symbol = symbol.upper() if symbol else None
        found = [e for e in self.events.values()
                 if start <= e.date <= end and (symbol is None or e.symbol == symbol)]
        return sorted(found, key=lambda e: (e.date, e.symbol))

    def blocking_reasons(self, symbol: str, today: date) -> list[str]:
        """Results or board meetings today or on the next trading day make an overnight hold a gap-risk gamble."""
        last = next_trading_day(today, self.holidays)
        return [f"{e.type.replace('_', ' ')} on {e.date:%d-%b}" + (f" ({e.note})" if e.note else "")
                for e in self.between(today, last, symbol) if e.type in BLOCKING_TYPES]

    def deal_notes(self, symbol: str, today: date, lookback_days: int = 3) -> list[str]:
        start = today - timedelta(days=lookback_days)
        return [f"{e.type.replace('_', ' ')} on {e.date:%d-%b}" + (f": {e.note}" if e.note else "")
                for e in self.between(start, today, symbol) if e.type in DEAL_TYPES]


def filter_candidates(candidates: list[dict], calendar: EventCalendar, today: date,
                      limit: int) -> tuple[list[dict], list[str]]:
    """Drop stocks with results/board meetings due; keep the first `limit` others, with deal notes."""
    kept, notes = [], []
    for c in candidates:
        reasons = calendar.blocking_reasons(c["symbol"], today)
        if reasons:
            notes.append(f"{c['symbol']}: excluded by calendar ({'; '.join(reasons)})")
            continue
        notes += [f"{c['symbol']}: recent {deal}" for deal in calendar.deal_notes(c["symbol"], today)]
        kept.append(c)
        if len(kept) == limit:
            break
    return kept, notes
