from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from btst.agents import CATALYST_TOOL, Agents, AgentError
from btst.journal import Journal
from btst.risk import build_plan, round_tick
from btst.screener import evaluate, with_today

TODAY = date(2026, 9, 28)


def _history(n=80, start=100.0, step=0.3, volume=1_000_000):
    rows = []
    for i in range(n):
        close = start + i * step
        rows.append({"open": close - 0.5, "high": close + 1, "low": close - 1, "close": close,
                     "volume": volume, "date": TODAY - timedelta(days=n - i)})
    return pd.DataFrame(rows)


def _quote(prev_close, ltp, high, low, volume, upper=None):
    return {"last_price": ltp, "volume": volume, "upper_circuit_limit": upper or ltp * 1.2,
            "ohlc": {"open": prev_close, "high": high, "low": low, "close": prev_close}}


def test_strong_close_with_volume_passes():
    hist = _history()
    prev = hist["close"].iloc[-1]
    quote = _quote(prev, prev * 1.03, prev * 1.031, prev * 0.995, 3_000_000)
    c = evaluate("ABC", "1", with_today(hist, quote, TODAY), quote, min_turnover_cr=5)
    assert c is not None
    assert c.close_position > 0.9 and c.volume_ratio == 3.0 and c.breakout_20d
    assert c.score > 80


def test_weak_close_rejected():
    hist = _history()
    prev = hist["close"].iloc[-1]
    quote = _quote(prev, prev * 1.01, prev * 1.04, prev * 0.99, 3_000_000)
    assert evaluate("ABC", "1", with_today(hist, quote, TODAY), quote, min_turnover_cr=5) is None


def test_near_upper_circuit_rejected():
    hist = _history()
    prev = hist["close"].iloc[-1]
    ltp = prev * 1.05
    quote = _quote(prev, ltp, ltp, prev, 3_000_000, upper=ltp)
    assert evaluate("ABC", "1", with_today(hist, quote, TODAY), quote, min_turnover_cr=5) is None


def test_with_today_replaces_existing_candle():
    hist = _history()
    hist.loc[len(hist)] = {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "date": TODAY}
    df = with_today(hist, _quote(100, 105, 106, 99, 5), TODAY)
    assert (df["date"] == TODAY).sum() == 1 and df.iloc[-1]["close"] == 105


CANDIDATES = [
    {"symbol": "AAA", "security_id": "1", "ltp": 500.0, "score": 80},
    {"symbol": "BBB", "security_id": "2", "ltp": 1000.0, "score": 90},
    {"symbol": "CCC", "security_id": "3", "ltp": 200.0, "score": 95},
]
REVIEWS = {
    "AAA": {"catalyst_score": 2, "veto": False, "red_flags": [], "summary": "order win"},
    "BBB": {"catalyst_score": 0, "veto": False, "red_flags": [], "summary": "no news"},
    "CCC": {"catalyst_score": 1, "veto": True, "red_flags": ["results tomorrow"], "summary": ""},
}
RISK = dict(capital_per_trade=20000, max_positions=3, available_funds=100000,
            stop_loss_pct=1.0, target_pct=2.0, realized_pnl_today=0, max_daily_loss=2000)


def test_plan_ranks_sizes_and_respects_veto():
    plans, notes = build_plan(CANDIDATES, REVIEWS, {"allow_new_positions": True}, **RISK)
    assert [p.symbol for p in plans] == ["AAA", "BBB"]
    aaa = plans[0]
    assert aaa.entry_limit == 501.0 and aaa.qty == 39
    assert aaa.stop_loss == round_tick(501 * 0.99) and aaa.target == round_tick(501 * 1.02)
    assert any("CCC" in n and "vetoed" in n for n in notes)


def test_market_agent_can_block_everything():
    plans, notes = build_plan(CANDIDATES, REVIEWS, {"allow_new_positions": False, "reasons": ["US CPI"]}, **RISK)
    assert plans == [] and "US CPI" in notes[0]


def test_daily_loss_limit_blocks():
    plans, _ = build_plan(CANDIDATES, REVIEWS, {"allow_new_positions": True},
                          **{**RISK, "realized_pnl_today": -2500})
    assert plans == []


def test_funds_cap_position_size():
    plans, _ = build_plan(CANDIDATES, REVIEWS, {"allow_new_positions": True},
                          **{**RISK, "available_funds": 25000})
    assert sum(p.qty * p.entry_limit for p in plans) <= 25000


def test_journal_roundtrip(tmp_path):
    j = Journal(tmp_path / "j.db")
    plan = {"symbol": "AAA", "security_id": "1", "qty": 10, "entry_limit": 100.0,
            "stop_loss": 99.0, "target": 102.0, "reason": "x"}
    j.record_buy("paper", plan, None)
    [t] = j.open_trades("paper", bought_before=date.today() + timedelta(days=1))
    j.record_exit(t["id"], 102.0, "TARGET", None)
    assert j.realized_pnl(date.today()) == 20.0
    assert j.open_trades("paper", bought_before=date.today() + timedelta(days=1)) == []


class _FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _agents_with(responses):
    agents = Agents.__new__(Agents)
    agents.model = "test"
    fake = _FakeMessages(responses)
    agents.client = SimpleNamespace(beta=SimpleNamespace(messages=fake))
    return agents, fake


def test_agent_loop_resumes_pause_and_returns_submission():
    submit = SimpleNamespace(type="tool_use", name="submit_catalyst_review",
                             input={"reviews": [{"symbol": "AAA", "catalyst_score": 1, "veto": False,
                                                 "red_flags": [], "summary": "ok"}]})
    agents, fake = _agents_with([
        SimpleNamespace(stop_reason="pause_turn", content=[SimpleNamespace(type="text", text="...")]),
        SimpleNamespace(stop_reason="tool_use", content=[submit]),
    ])
    assert agents.catalysts([{"symbol": "AAA"}])["AAA"]["catalyst_score"] == 1
    assert len(fake.calls) == 2 and fake.calls[1]["messages"][-1]["role"] == "assistant"


def test_agent_refusal_raises():
    agents, _ = _agents_with([SimpleNamespace(stop_reason="refusal", stop_details=None, content=[])])
    with pytest.raises(AgentError):
        agents._run("sys", "prompt", CATALYST_TOOL)


def _gemini_with(response):
    from btst.gemini_agents import GeminiAgents
    agents = GeminiAgents.__new__(GeminiAgents)
    agents.model = "test"
    calls = []
    agents.client = SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda **kw: calls.append(kw) or response))
    return agents, calls


def test_gemini_catalysts_parse_json_with_search_and_schema():
    body = '{"reviews": [{"symbol": "AAA", "catalyst_score": 2, "veto": false, "red_flags": [], "summary": "order win"}]}'
    agents, calls = _gemini_with(SimpleNamespace(text=body, candidates=[]))
    assert agents.catalysts([{"symbol": "AAA"}])["AAA"]["catalyst_score"] == 2
    config = calls[0]["config"]
    assert config.tools[0].google_search is not None
    assert config.response_json_schema == CATALYST_TOOL["input_schema"]


def test_gemini_empty_answer_raises():
    agents, _ = _gemini_with(SimpleNamespace(text=None, candidates=[SimpleNamespace(finish_reason="SAFETY")],
                                             prompt_feedback=None))
    with pytest.raises(AgentError, match="SAFETY"):
        agents.market_context({})
