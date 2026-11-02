# Cowork Setup for BTST Self-Improving Subagents

Research only. Nothing here places orders; you execute any trades yourself. Not financial advice.

---

## 1. Install or Enable the Plugin
- Claude Desktop -> Cowork -> Customize (or Plugins).
- Enable `btst-agents`.
- The 4 subagents will be active:
  1. `btst-screener-315pm`
  2. `btst-morning-845am`
  3. `btst-learner-345pm`
  4. `btst-market-shield`

---

## 2. Connect Zerodha Kite MCP
- Settings -> Connectors -> add Zerodha Kite (`https://mcp.kite.trade/mcp`) and authenticate each morning.
- Tools used: `mcp__Kite_mcp__get_ltp`, `mcp__Kite_mcp__get_ohlc`, `mcp__Kite_mcp__get_quotes`, `mcp__Kite_mcp__get_holdings`, `mcp__Kite_mcp__get_positions`.

---

## 3. Daily Scheduled Tasks & Prompts (Weekdays, IST)

### **Cycle 1: 3:15 PM IST (BTST Selection)**
> Run `btst-screener-315pm`. First check `review/lessons.md` for negative rules. Using Kite quotes, screen today's top NSE F&O gainers and losers. Filter for Long Buildup (Price ↑ + OI ↑) and veto Short Covering. Confirm price is closing in the upper 15% of the day's range. Veto any stock with quarterly results today or tomorrow, or on the F&O ban list. Save up to 10 buys and 10 sell ideas with stop -1% and target +2% to `data/picks-<date>.json`.

### **Cycle 2: 8:45 AM IST Next Day (Pre-Market Audit & Exit Plan)**
> Run `btst-morning-845am`. Load yesterday's `data/picks-<date>.json`. Research GIFT Nifty, US close, Asian markets, overnight stock news, and today's NSE F&O ban list. Formulate the 9:15–9:45 AM exit directives (SELL AT OPEN if target reached or stop broken; HOLD TO 9:45 otherwise). Save the brief to `data/brief-<date>.md`.

### **Cycle 3: 3:45 PM IST (Evaluation & Self-Learning Loop)**
> Run `btst-learner-345pm`. Load yesterday's `data/picks-<date>.json`. Using Kite MCP, fetch today's actual OHLC and LTP for each stock. Compare with expected moves: check if target (+2%) or stop-loss (-1%) was hit. Conduct root-cause post-mortem on any failed trade. Append newly formulated negative rules to `review/lessons.md` so the mistake is never repeated. Update `review/review-log.json` and save the report to `review/review-<date>.md`.

---

## 4. Safety & Rules
- **Earnings Veto**: Never hold a stock overnight if quarterly results are due today or tomorrow.
- **Cash Limitation**: In Indian cash equity, overnight shorts are not permitted (STBT can only be done via Stock Futures or Options).
- **Orders**: Subagents never place or alter orders.
