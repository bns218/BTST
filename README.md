# BTST Autonomous Subagents Suite for NSE F&O

A self-improving, research-only subagent suite for Indian Equities (NSE F&O) running **BTST** (*Buy Today, Sell Tomorrow*) and **STBT** (*Sell Today, Buy Tomorrow*) momentum workflows with real-time **Zerodha Kite MCP** integration.

---

## Key Highlights

- **Closed-Loop Daily Learning**: Evaluates yesterday's picks against real Kite OHLC market data at 3:45 PM IST, diagnoses failed trades, and logs negative filter rules to `review/lessons.md` so the system never repeats past mistakes.
- **Derivative OI Buildup Analysis**: Filters for genuine **Long Buildup** (Price ↑ + OI ↑) and filters out dangerous **Short Covering** traps.
- **Closing Strength Filter**: Enforces end-of-day momentum (stocks must close in the upper 15% of the day's candle range).
- **Quarterly Earnings & Ban Veto**: Strict zero-tolerance veto for stocks reporting quarterly results today or tomorrow, or on the NSE F&O ban list.
- **Strict 9:15 – 9:45 AM Exit Discipline**: Pre-market 8:45 AM brief assessing GIFT Nifty gap risk and clear exit benchmarks (-1% stop, +2% target).
- **Safe & Non-Custodial**: Strictly research and advisory. Agents never place or modify broker orders.

---

## The Subagents Suite

| Subagent | Timing | Role & Tools |
| :--- | :--- | :--- |
| **[`1-btst-screener-315pm`](file:///c:/Users/nagas/Desktop/BTST/agents/1-btst-screener-315pm.md)** | **3:15 PM IST** | Scans top F&O gainers/losers, filters OI buildup & day's high close, vetoes earnings, reads `review/lessons.md`, and generates `data/picks-<date>.json`. |
| **[`2-btst-morning-845am`](file:///c:/Users/nagas/Desktop/BTST/agents/2-btst-morning-845am.md)** | **8:45 AM IST** | Audits yesterday's picks against GIFT Nifty, overnight news, and today's ban list. Prepares 9:15-9:45 AM exit plan in `data/brief-<date>.md`. |
| **[`3-btst-learner-345pm`](file:///c:/Users/nagas/Desktop/BTST/agents/3-btst-learner-345pm.md)** | **3:45 PM IST** | Fetches actual Kite OHLC data, checks if targets/stops were hit, performs root-cause diagnostics, and updates `review/lessons.md` & `review/review-log.json`. |
| **[`4-btst-market-shield`](file:///c:/Users/nagas/Desktop/BTST/agents/4-btst-market-shield.md)** | **3:00 PM IST** | Evaluates Nifty 50, Bank Nifty, India VIX, FII/DII flows, and global binary events to set the overnight risk verdict. |

---

## Daily Schedule & Prompts

Refer to [`WORKFLOW.md`](file:///c:/Users/nagas/Desktop/BTST/WORKFLOW.md) for full instructions, daily prompts, and operational details.
