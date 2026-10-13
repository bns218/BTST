from datetime import date

import pytest

from btst.review import (Pick, add_picks, eval_day, format_summary, pending, score_pending, score_pick, summarize)

D = date(2026, 10, 14)   # a Wednesday
BAR = lambda o, h, l, c: {"open": o, "high": h, "low": l, "close": c}


def test_eval_day_am_same_day_pm_next_trading_day():
    assert eval_day(Pick(D, "am", "buy", "A", 100)) == D
    assert eval_day(Pick(D, "pm", "buy", "A", 100)) == date(2026, 10, 15)
    assert eval_day(Pick(date(2026, 10, 16), "pm", "buy", "A", 100)) == date(2026, 10, 19)   # Friday -> Monday


def test_pm_buy_is_judged_on_next_open_and_levels_use_high_low():
    p = Pick(D, "pm", "buy", "A", 100, stop=99, target=102)
    r = score_pick(p, BAR(100.5, 102.5, 100.2, 101.0))
    assert r["move_pct"] == 0.5 and r["correct"] and r["outcome"] == "target"
    assert not score_pick(p, BAR(99.4, 100, 99.1, 99.8))["correct"]
    assert score_pick(p, BAR(98.0, 99, 97, 98.5))["outcome"] == "gap_through_stop"
    assert score_pick(p, BAR(100.5, 102.5, 98.5, 100))["outcome"] == "ambiguous"


def test_am_sell_is_judged_on_close_and_mirrors_levels():
    p = Pick(D, "am", "sell", "B", 200, stop=202, target=196)
    r = score_pick(p, BAR(199, 201, 195.5, 197))
    assert r["correct"] and r["move_pct"] == -1.5 and r["outcome"] == "target"
    assert not score_pick(p, BAR(201, 203, 200, 202.5))["correct"]


def test_default_levels_when_missing():
    assert score_pick(Pick(D, "pm", "buy", "A", 100), BAR(100, 102.1, 100, 101))["outcome"] == "target"


def test_bad_pick_rejected():
    with pytest.raises(ValueError):
        Pick(D, "noon", "buy", "A", 100)


def test_log_pending_score_and_summary(tmp_path):
    picks, results = tmp_path / "picks.csv", tmp_path / "results.csv"
    batch = [Pick(D, "pm", "buy", "A", 100, 99, 102, "news|sector"), Pick(D, "pm", "buy", "B", 50, 49.5, 51, "news"),
             Pick(D, "am", "sell", "C", 200, 202, 196, "sector")]
    assert add_picks(picks, batch) == 3 and add_picks(picks, batch) == 0          # no duplicates
    # on the pick day only the am pick is due
    assert [p.symbol for p, _ in pending(picks, results, D)] == ["C"]
    bars = {"2026-10-14": {"C": BAR(199, 200, 195, 197)},
            "2026-10-15": {"A": BAR(101, 102.5, 100.5, 101.5), "B": BAR(49, 49.2, 48.5, 48.8)}}
    scored, missing = score_pending(picks, results, bars, date(2026, 10, 15))
    assert scored == 3 and not missing
    assert score_pending(picks, results, bars, date(2026, 10, 15)) == (0, [])      # idempotent
    s = summarize(results)
    assert s["overall"]["n"] == 3 and s["overall"]["correct"] == 2
    assert s["by_group"]["pm/buy"]["correct"] == 1 and s["by_tag"]["news"]["n"] == 2
    assert "2/3 picks moved the right way" in format_summary(s)


def test_missing_bars_reported_and_retried(tmp_path):
    picks, results = tmp_path / "p.csv", tmp_path / "r.csv"
    add_picks(picks, [Pick(D, "am", "buy", "A", 100)])
    assert score_pending(picks, results, {}, D) == (0, ["2026-10-14 A"])
    assert score_pending(picks, results, {"2026-10-14": {"A": BAR(100, 101, 99, 100.5)}}, D)[0] == 1


def test_edge_counts_sells_in_their_own_direction(tmp_path):
    picks, results = tmp_path / "p.csv", tmp_path / "r.csv"
    add_picks(picks, [Pick(D, "am", "buy", "A", 100), Pick(D, "am", "sell", "B", 100)])
    bars = {D.isoformat(): {"A": BAR(100, 102, 100, 102), "B": BAR(100, 100, 98, 98)}}
    score_pending(picks, results, bars, D)
    s = summarize(results)
    assert s["overall"]["avg_edge_pct"] == 2.0 and s["by_group"]["am/sell"]["avg_edge_pct"] == 2.0
