---
description: Run the 3 PM BTST workflow with subagents (screen, market context, catalysts, risk gate). Never places orders.
argument-hint: "[scan|movers] (default: scan)"
---

Run the BTST workflow for today in mode `$ARGUMENTS` (use `scan` if empty; `movers` means the top 20 F&O gainers and losers, giving up to 10 buy picks and up to 10 sell ideas). Work from the repo root and activate `.venv` if it exists. NEVER run `python -m btst buy`, place orders, or use any trading tool: stop after showing the plan.

1. Screen with code: `python -m btst <mode>`. It writes `data/shortlist-<today>.json` (calendar-vetoed stocks are already removed). If nothing passes, say so and stop.
2. Read that file. Launch BOTH subagents in parallel in a single message:
   - `btst-market-context`: pass the file's `index_snapshot` and `notes`.
   - `btst-catalyst-analyst`: pass the symbols and % moves from `shortlist` (side `long`; for `movers` also a second call with side `short` for the `losers` symbols, in the same message).
3. Save the market JSON to `data/market-<today>.json`. Merge all catalyst reviews into one `{"reviews": [...]}` and save it to `data/reviews-<today>.json` (both must be valid JSON).
4. Risk gate in code: `python -m btst plan --market data/market-<today>.json --reviews data/reviews-<today>.json`.
5. Show the user the market verdict, the plan (buy limit, stop, target, quantity, one-line reason per stock), vetoed stocks and why, and for `movers` the SELL ideas (intraday or stock-futures only; cash BTST cannot short overnight).
6. Finish with: "Place these yourself as CNC limit orders before 3:30 PM. Not financial advice."
