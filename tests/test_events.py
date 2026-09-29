from datetime import date

import pytest

from btst.events import Event, EventCalendar, next_trading_day


def test_next_trading_day_skips_weekend_and_holiday():
    assert next_trading_day(date(2026, 9, 29)) == date(2026, 9, 30)
    assert next_trading_day(date(2026, 10, 2)) == date(2026, 10, 5)
    assert next_trading_day(date(2026, 10, 1), frozenset({date(2026, 10, 2)})) == date(2026, 10, 5)


def test_results_tomorrow_or_today_block_but_later_ones_do_not(tmp_path):
    cal = EventCalendar(tmp_path / "c.csv")
    cal.add(Event("tcs", "results", date(2026, 10, 8), "Q2"))
    assert cal.blocking_reasons("TCS", date(2026, 10, 7))
    assert cal.blocking_reasons("TCS", date(2026, 10, 8))
    assert not cal.blocking_reasons("TCS", date(2026, 10, 6))
    assert not cal.blocking_reasons("TCS", date(2026, 10, 9))


def test_friday_scan_blocks_monday_results(tmp_path):
    cal = EventCalendar(tmp_path / "c.csv")
    cal.add(Event("INFY", "results", date(2026, 10, 5)))
    assert cal.blocking_reasons("INFY", date(2026, 10, 2))
    assert not cal.blocking_reasons("INFY", date(2026, 10, 1))


def test_deal_notes_are_informational_not_blocking(tmp_path):
    cal = EventCalendar(tmp_path / "c.csv")
    cal.add(Event("ADANIENT", "block_deal", date(2026, 9, 25), "promoter transfer"))
    assert not cal.blocking_reasons("ADANIENT", date(2026, 9, 28))
    assert cal.deal_notes("ADANIENT", date(2026, 9, 28))
    assert not cal.deal_notes("ADANIENT", date(2026, 10, 5))


def test_csv_roundtrip_dedupes(tmp_path):
    path = tmp_path / "c.csv"
    cal = EventCalendar(path)
    cal.add(Event("TCS", "results", date(2026, 10, 8), "old"))
    cal.add(Event("TCS", "results", date(2026, 10, 8), "new"))
    cal.save()
    again = EventCalendar(path)
    assert len(again.events) == 1 and next(iter(again.events.values())).note == "new"


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        Event("TCS", "rumour", date(2026, 10, 8))


def test_filter_candidates_drops_results_stocks_and_notes_deals(tmp_path):
    from btst.events import filter_candidates
    cal = EventCalendar(tmp_path / "c.csv")
    cal.add(Event("AAA", "results", date(2026, 10, 8)))
    cal.add(Event("BBB", "block_deal", date(2026, 10, 6), "PE exit"))
    cands = [{"symbol": s} for s in ("AAA", "BBB", "CCC", "DDD")]
    kept, notes = filter_candidates(cands, cal, date(2026, 10, 7), limit=2)
    assert [c["symbol"] for c in kept] == ["BBB", "CCC"]
    assert any("AAA" in n and "excluded" in n for n in notes) and any("BBB" in n and "PE exit" in n for n in notes)
