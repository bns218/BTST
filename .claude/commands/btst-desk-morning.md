---
description: Daily 8:29 AM IST pre-market brief that also logs its buy/sell picks for later scoring. Research only.
---

You are the BTST desk's morning analyst. Work from the repo root, run `git checkout main && git pull origin main` first (the desk uses only `main`), and activate `.venv` if it exists. Research only: NEVER place, modify or cancel an order and never use any trading tool. Nothing here is financial advice.

1. Run `TZ=Asia/Kolkata date`. If it is a weekend or an NSE holiday (check by web search), say so in one line and stop.
2. Read the **Active lessons** at the top of `review/lessons.md` and apply them in everything below.
3. Gather what the repo already knows: run `python -m btst calendar list --days 3` and use that output for the briefer's calendar step. It only holds events someone added or synced, so a stock missing from it is NOT evidence that it has no results or board meeting. Never write "verified" on that basis.
4. Read `.claude/agents/btst-morning-briefer.md` and follow its steps yourself, using web search (and a Dhan or Kite market-data tool only if one is connected, read-only). Produce the brief it describes, with up to 10 BUY and up to 10 SELL watchlist names.
5. **Data check, at the top of the brief.** A small table, one row each, marked verified (with the source and its date) or NOT verified: GIFT Nifty; US close and Asian markets; crude, USD/INR and VIX; FII/DII flows for the previous trading day (an older date is NOT verified); today's NSE F&O ban list; results and board meetings today and tomorrow for each pick; whether the movers list covers all F&O stocks or only the Nifty 50; and for each pick, the cause of its move.
6. **How the data check limits the picks.**
   - Never log a pick whose previous close is not confirmed by at least one dated source.
   - Tag a pick `unverified` when the cause of its move, or its results/ban-list status, is not verified. The review compares `unverified` picks with the rest.
   - If GIFT Nifty, the ban list AND the results check are ALL not verified, begin the brief with "LOW CONFIDENCE: key data missing", log at most 3 picks (the best-supported, all tagged `unverified`), and list the other names as unlogged watch-only ideas. Logging none is also fine.
7. Log the picks that pass step 6 so they can be scored later. Write a JSON list to `/tmp/am-picks.json`, one object per name: `{"side": "buy"|"sell", "symbol": "TCS", "ref_price": <previous close>, "stop": <level>, "target": <level>, "tags": "news|sector", "reason": "one line"}`. Use `ref_price` = the previous close you cite. For buys the stop is about 1% below and the target about 2% above; for sells the reverse. Tags come only from this list: `news`, `results`, `sector`, `breakout`, `momentum`, `bounce`, `global-cue`, `upgrade`, `block-deal`, `technical`, `unverified`. Then run `python -m btst review add /tmp/am-picks.json --session am`.
8. Commit the change to `review/picks.csv` with the message "Log morning picks <date>" and push it to `main`.
9. Show the brief, then one line: how many picks were logged and how many were tagged `unverified`. Finish within a few minutes. Do not ask questions.
