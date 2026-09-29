from datetime import date, datetime, timedelta

import requests

from .events import Event, EventCalendar

HOME = "https://www.nseindia.com"
BOARD_MEETINGS = HOME + "/api/corporate-board-meetings"
LARGE_DEALS = HOME + "/api/snapshot-capital-market-largedeal"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": HOME + "/",
}


def _parse_date(text: str | None) -> date | None:
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((text or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_board_meetings(payload) -> list[Event]:
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    events = []
    for row in rows:
        symbol, when = (row.get("symbol") or "").strip(), _parse_date(row.get("bm_date"))
        if not symbol or not when:
            continue
        purpose = " ".join(filter(None, [row.get("purpose"), row.get("bm_desc")])).strip()
        kind = "results" if "result" in purpose.lower() else "board_meeting"
        events.append(Event(symbol, kind, when, purpose[:120], "NSE board meetings"))
    return events


def parse_large_deals(payload) -> list[Event]:
    events = []
    for key, kind in (("BULK_DEALS_DATA", "bulk_deal"), ("BLOCK_DEALS_DATA", "block_deal")):
        for row in payload.get(key, []):
            symbol, when = (row.get("symbol") or "").strip(), _parse_date(row.get("date"))
            if not symbol or not when:
                continue
            note = f"{row.get('buySell', '')} {row.get('qty', '')} @ {row.get('watp', '')} by {row.get('clientName', '')}"
            events.append(Event(symbol, kind, when, note.strip()[:120], "NSE large deals"))
    return events


class NSE:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self._warm = False

    def _get(self, url: str, params: dict | None = None):
        if not self._warm:
            self.session.get(HOME, timeout=10)
            self._warm = True
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def board_meetings(self, start: date, end: date) -> list[Event]:
        params = {"index": "equities", "from_date": start.strftime("%d-%m-%Y"), "to_date": end.strftime("%d-%m-%Y")}
        return parse_board_meetings(self._get(BOARD_MEETINGS, params))

    def large_deals(self) -> list[Event]:
        return parse_large_deals(self._get(LARGE_DEALS))


def sync_calendar(calendar: EventCalendar, nse: NSE, symbols: set[str], today: date, days: int = 45) -> int:
    """Pull board meetings (next `days`) and latest bulk/block deals for `symbols` into the calendar."""
    wanted = {s.upper() for s in symbols}
    added = 0
    for event in nse.board_meetings(today - timedelta(days=1), today + timedelta(days=days)) + nse.large_deals():
        if event.symbol.upper() in wanted:
            calendar.add(event)
            added += 1
    calendar.save()
    return added
