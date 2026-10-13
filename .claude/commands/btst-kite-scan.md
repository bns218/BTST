---
description: 3 PM BTST workflow using the Kite MCP for market data (no Dhan or API keys). Never places orders.
argument-hint: "[btst|movers] (default: movers)"
---

Run the BTST workflow for today in mode `$ARGUMENTS` (use `movers` if empty: the top 20 F&O gainers and top 20 losers are screened, giving up to 10 buy picks and up to 10 sell ideas; `btst` = the stricter buy-only screen). Work from the repo root and activate `.venv` if it exists. NEVER place orders: do not call any Kite order tool (`place_order`, `modify_order`, `cancel_order`, GTT tools) and do not run `python -m btst buy`.

1. Kite login: call `mcp__kite__get_profile`. If it fails because you are not logged in, call `mcp__kite__login`, give the user the login URL, wait for them to finish, then retry. Stop if it still fails.
2. Read `universe.txt` (skip `#` lines). Build the instrument list `NSE:<SYMBOL>` for every stock, plus `NSE:NIFTY 50`, `NSE:NIFTY BANK`, `NSE:INDIA VIX`. Call `mcp__kite__get_quotes` for the whole list (split into chunks of at most 500 if the tool requires it, and merge the results into one JSON object).
3. Save the combined quotes JSON to `data/kite-quotes-<today>.json` with the Write tool, VERBATIM: do not round, drop or summarize any field. It must be valid JSON containing every stock.
4. Screen in code: `python -m btst kite-screen --quotes data/kite-quotes-<today>.json --mode <btst|movers> --top 20` (use `--top 10` for `btst`). If it refuses because stocks are missing from the quotes, re-fetch the missing symbols and merge; do not rank a partial list. If nothing passes, say so and stop. This screen uses only the live quote (move, close position, turnover, order book), not price history, so tell the user it is a lighter filter than `scan`.
5. Read `data/shortlist-<today>.json`. Launch BOTH subagents in parallel in one message: `btst-market-context` (pass `index_snapshot` and `notes`) and `btst-catalyst-analyst` called with side `long` for the `shortlist` symbols and % moves; in `movers` mode ALSO a second call with side `short` for the `losers` symbols, in the same message.
6. Save the market JSON verbatim to `data/market-<today>.json`. Merge the catalyst reviews (long and short calls) into one `{"reviews": [...]}` and save it to `data/reviews-<today>.json` (both files must be valid JSON).
7. Risk gate in code: `python -m btst plan --market data/market-<today>.json --reviews data/reviews-<today>.json`.
8. Show the market verdict, then two lists: up to 10 BUY picks (buy limit, stop, target, quantity, reason) and, in `movers` mode, up to 10 SELL ideas (sell limit, stop above, target below, reason), plus vetoed stocks and why. Sell ideas are intraday or stock-futures trades: cash BTST cannot short overnight, so say so and do not suggest holding a short overnight in cash.
9. Finish with: "Place these in Kite yourself as CNC limit orders before 3:30 PM. Plans from Kite data cannot be placed by `python -m btst buy` in live mode. Not financial advice."
