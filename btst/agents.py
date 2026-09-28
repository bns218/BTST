import json
import logging
from datetime import date

import anthropic

log = logging.getLogger(__name__)

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}

MARKET_CONTEXT_TOOL = {
    "name": "submit_market_context",
    "description": "Submit your final market-context assessment. Call exactly once, when done researching.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["bias", "allow_new_positions", "reasons"],
        "properties": {
            "bias": {"type": "string", "enum": ["bullish", "neutral", "bearish"]},
            "allow_new_positions": {
                "type": "boolean",
                "description": "False if overnight risk is high enough that no BTST trade should be taken today.",
            },
            "reasons": {"type": "array", "items": {"type": "string"}},
        },
    },
}

CATALYST_TOOL = {
    "name": "submit_catalyst_review",
    "description": "Submit your per-stock catalyst review. Call exactly once, covering every candidate.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reviews"],
        "properties": {
            "reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["symbol", "catalyst_score", "veto", "red_flags", "summary"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "catalyst_score": {
                            "type": "integer",
                            "description": "-2 (strongly negative news) to +2 (strong fresh positive catalyst); 0 if nothing notable.",
                        },
                        "veto": {
                            "type": "boolean",
                            "description": "True if the stock must not be held overnight (results/board meeting tomorrow, "
                                           "regulatory action, pledge invocation, ASM/T2T move, fraud allegations, etc.).",
                        },
                        "red_flags": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                    },
                },
            }
        },
    },
}

MARKET_CONTEXT_SYSTEM = """You are the market-context analyst in a BTST (buy today, sell tomorrow) trading system \
for Indian equities (NSE). Your job is to judge overnight risk for holding long cash positions until tomorrow morning.

Research today's session using web search: Nifty 50 and Bank Nifty close and breadth, India VIX, FII/DII flows, \
GIFT Nifty, US futures and Asian markets, crude oil, USD/INR, and any scheduled events before tomorrow's open \
(RBI policy, US CPI/FOMC, budget, election results, geopolitical news).

Be skeptical and concise. Only set allow_new_positions to false for genuine elevated overnight risk, not ordinary \
volatility. Cite concrete facts in your reasons."""

CATALYST_SYSTEM = """You are the news and catalyst analyst in a BTST (buy today, sell tomorrow) trading system for \
Indian equities (NSE). A quantitative screener has already shortlisted stocks with strong price/volume action today. \
For each one, find out *why* it moved and whether holding it overnight is dangerous.

Use web search to check today's exchange announcements and news for each stock: results, order wins, block deals, \
brokerage upgrades/downgrades, promoter pledges, SEBI/regulatory action, upcoming board meetings or results \
(especially tomorrow), and any move into ASM/GSM/T2T surveillance.

Do not re-judge the chart; the screener handles price action. Set veto=true only for concrete overnight risks. \
If you find nothing notable, use catalyst_score 0 and say so. Cover every candidate symbol exactly once."""


class AgentError(RuntimeError):
    pass


class Agents:
    def __init__(self, model: str):
        self.client = anthropic.Anthropic()
        self.model = model

    def _run(self, system: str, prompt: str, submit_tool: dict) -> dict:
        messages: list = [{"role": "user", "content": prompt}]
        for _ in range(8):
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=f"{system}\n\nFinish by calling {submit_tool['name']}.",
                messages=messages,
                tools=[WEB_SEARCH, submit_tool],
                thinking={"type": "adaptive"},
                output_config={"effort": "medium"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if response.stop_reason == "refusal":
                raise AgentError(f"Model refused: {response.stop_details}")
            for block in response.content:
                if block.type == "tool_use" and block.name == submit_tool["name"]:
                    return block.input
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "pause_turn":
                messages.append({"role": "user", "content": f"Call {submit_tool['name']} now with your findings."})
        raise AgentError(f"Agent never called {submit_tool['name']}")

    def market_context(self, index_snapshot: dict) -> dict:
        return self._run(MARKET_CONTEXT_SYSTEM, market_prompt(index_snapshot), MARKET_CONTEXT_TOOL)

    def catalysts(self, candidates: list[dict]) -> dict[str, dict]:
        result = self._run(CATALYST_SYSTEM, catalyst_prompt(candidates), CATALYST_TOOL)
        return {r["symbol"]: r for r in result["reviews"]}


def market_prompt(index_snapshot: dict) -> str:
    return (f"Today is {date.today():%A %d %B %Y}. Live index snapshot from the broker:\n"
            f"{json.dumps(index_snapshot, indent=2)}\n\nAssess overnight risk for new BTST longs.")


def catalyst_prompt(candidates: list[dict]) -> str:
    return (f"Today is {date.today():%A %d %B %Y}. Screener shortlist (NSE symbols with today's metrics):\n"
            f"{json.dumps(candidates, indent=2)}\n\nReview each for catalysts and overnight red flags.")
