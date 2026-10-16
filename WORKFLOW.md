# Daily BTST Operational Workflow & Instructions

A self-improving, research-only autonomous subagent workflow for Indian Equities (NSE F&O) BTST (Buy Today, Sell Tomorrow) and STBT momentum trading.

---

## The 3 Daily Operational Cycles

```
   ┌────────────────────────────────────────────────────────┐
   │                  3:15 PM IST (Daily)                   │
   │  • Run: btst-screener-315pm                            │
   │  • Reads: review/lessons.md                            │
   │  • Screens: F&O gainers/losers + OI Buildup + Earnings │
   │  • Outputs: data/picks-<date>.json                     │
   └──────────────────────────┬─────────────────────────────┘
                              │
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │                 8:45 AM IST (Next Day)                 │
   │  • Run: btst-morning-845am                             │
   │  • Audits: GIFT Nifty, overnight news, today's ban     │
   │  • Prepares: 9:15-9:45 AM exit plan                    │
   │  • Outputs: data/brief-<date>.md                       │
   └──────────────────────────┬─────────────────────────────┘
                              │
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │                 3:45 PM IST (Next Day)                 │
   │  • Run: btst-learner-345pm                             │
   │  • Evaluates: Real Kite OHLC data vs expected moves    │
   │  • Diagnoses: Root causes of failed trades             │
   │  • Updates: review/lessons.md (Do not repeat!)         │
   │  • Outputs: review/review-<date>.md & review-log.json  │
   └────────────────────────────────────────────────────────┘
```

---

## 1. Cycle 1: 3:15 PM IST — Stock Selection
**Objective**: Identify up to 5 top-conviction BTST buys and up to 5 STBT sells for the next trading day.

**Prompt to Run**:
> `Run btst-screener-315pm. Read review/lessons.md first. Scan top NSE F&O gainers and losers using Kite quotes, filter for Long Buildup (Price ↑ + OI ↑), verify day's high closing strength, and veto any stock with quarterly earnings today or tomorrow. Save the result to data/picks-<today-date>.json.`

**What the Agent Does**:
1. Checks `review/lessons.md` for past failure patterns to avoid.
2. Checks Kite MCP quotes for active F&O top gainers and losers.
3. Vetoes any fakeout rally driven by Short Covering (Price UP + OI DOWN).
4. Verifies closing strength in the upper 15% of the daily range.
5. Vetoes any stock reporting quarterly financial results today or tomorrow.
6. Writes structured entries, stops (-1%), and targets (+2%) to `data/picks-<date>.json`.

---

## 2. Cycle 2: 8:45 AM IST — Pre-Market Audit & Exit Plan
**Objective**: Audit overnight developments and formulate a strict 9:15–9:45 AM exit plan.

**Prompt to Run**:
> `Run btst-morning-845am. Load yesterday's data/picks-<yesterday-date>.json. Check GIFT Nifty, global overnight cues, overnight corporate announcements, and today's NSE F&O ban list. Generate the 9:15-9:45 AM exit gameplan and save it to data/brief-<today-date>.md.`

**What the Agent Does**:
1. Assesses GIFT Nifty opening gap expectation (gap-up, flat, gap-down).
2. Audits each carried position for overnight news or emergency ban additions.
3. Outlines exact exit rules:
   - **SELL AT OPEN (9:15 AM)**: If target (+2%) reached on gap-up or stop-loss (-1%) broken on gap-down.
   - **HOLD TO 9:45 AM**: Normal price continuation; exit into strength before 9:45 AM.
4. Saves the gameplan to `data/brief-<date>.md`.

---

## 3. Cycle 3: 3:45 PM IST — Real Market Evaluation & Self-Learning Loop
**Objective**: Test expected moves against actual Kite market data, diagnose errors, and update `review/lessons.md` so mistakes are never repeated.

**Prompt to Run**:
> `Run btst-learner-345pm. Load yesterday's data/picks-<yesterday-date>.json and fetch today's actual OHLC and LTP using Kite MCP. Check if expected moves happened, conduct root-cause diagnostics on any failed trade, update review/review-log.json, and append newly learned rules to review/lessons.md. Save the daily review to review/review-<today-date>.md.`

**What the Agent Does**:
1. Pulls real session Open, High, Low, and Close from Kite MCP.
2. Evaluates whether each pick hit target (+2%) or stop-loss (-1%).
3. Conducts a diagnostic post-mortem on any loss (Short covering trap? Late fade? Macro drag? Missed results?).
4. Formulates a new negative filter rule and appends it to `review/lessons.md`.
5. Updates cumulative accuracy metrics in `review/review-log.json`.

---

## Safety & Compliance
* **Research and advisory only**: Subagents never place, modify, or cancel broker orders.
* All trade decisions and executions remain under full human control.
