---
description: Run the 3 PM BTST workflow with subagents (screen, market context, catalysts, risk gate). Never places orders.
argument-hint: "[scan|movers] (default: scan)"
---

Run the BTST workflow for today in mode `$ARGUMENTS` (use `scan` if empty; `movers` means top 20 F&O gainers and losers). Work from the repo root and activate `.venv` if it exists. NEVER run `python -m btst buy`, place orders, or use any trading tool: stop after showing the plan.

1. Screen with code: `python -m btst <mode> --screen-only`. It writes `data/shortlist-<today>.json` (calendar-vetoed stocks are already removed). If nothing passes, say so and stop.
2. Read that file. Launch BOTH subagents in parallel in a single message:
   - `btst-market-context`: pass the file's `index_snapshot` and `notes`.
   - `btst-catalyst-analyst`: pass the symbols and % moves from `shortlist` (for `movers`, only the gainers; the `losers` list is a watchlist, so also pass those symbols in a second call and report them as watch-only).
3. Save the market JSON to `data/market-<today>.json` and the reviews JSON to `data/reviews-<today>.json` exactly as the agents returned them (strip any stray prose; both must be valid JSON).
4. Risk gate in code: `python -m btst plan --market data/market-<today>.json --reviews data/reviews-<today>.json`.
5. Show the user the market verdict, the plan (buy limit, stop, target, quantity, one-line reason per stock), vetoed stocks and why, and for `movers` the loser watchlist (no orders for losers: cash BTST cannot short overnight).
6. Finish with: "Review, then run `python -m btst buy` yourself. Paper mode unless LIVE_TRADING=true. Not financial advice." Do not run it for the user.
