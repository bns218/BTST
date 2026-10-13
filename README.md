# BTST

AI-assisted **Buy Today, Sell Tomorrow** trading for NSE equities, using **Dhan** for market data and orders and AI agents (**Gemini** or **Claude**, your choice) for news and risk judgement.

> Paper trading is the default. Nothing real is ordered until you set `LIVE_TRADING=true`. This is a tool, not financial advice. Test it thoroughly in paper mode first.

## How it works

```
~3:00 PM  scan    Screener (code) ─► top N ─► Market-context agent ─┐
                                        └──► Catalyst agent ──────┴─► Risk gate (code) ─► plan-YYYY-MM-DD.json
~3:15 PM  buy     You review the plan, confirm ─► CNC LIMIT buys on Dhan (or paper journal)
9:15 AM   exit    Polls LTP: sells on stop-loss / target, everything else at EXIT_BY (default 09:45)
anytime   report  Win rate and P&L from the journal
```

| Piece | Kind | Job |
|---|---|---|
| `screener.py` | Code | Strong close near day high, volume surge vs 20-day average, EMA20/50 trend, RSI, 20-day breakout, liquidity, and upper-circuit filters |
| Market-context agent | Gemini + Google Search, or Claude + web search | Checks global cues, GIFT Nifty, VIX, FII flows and event risk. Can block all new trades for the day |
| Catalyst agent | Gemini + Google Search, or Claude + web search | Finds why each stock moved. Vetoes stocks with results tomorrow, regulatory action, pledges, or ASM/T2T moves |
| `risk.py` | Code | Ranks, sizes and sets SL/target, and enforces max positions, capital per trade, available funds and daily loss limit. **Agents can only remove trades, never add or resize them.** |
| `journal.py` | SQLite | Every trade, fill and exit, for review and tuning |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN and your AI key
```

Pick the AI provider in `.env`:

- `LLM_PROVIDER=gemini` with `GEMINI_API_KEY` (from aistudio.google.com). Default model is `gemini-3.8-flash`; change it with `GEMINI_MODEL`.
- `LLM_PROVIDER=claude` with `ANTHROPIC_API_KEY`. Default model is `claude-opus-5`; change it with `CLAUDE_MODEL`.

The Dhan access token comes from web.dhan.co → My Profile → Access DhanHQ APIs. `universe.txt` lists every NSE F&O stock (207 as of 29-Sep-2026); edit it to change which stocks are scanned and calendar-checked.

## Daily use

```bash
python -m btst scan      # ~3:00-3:10 PM IST
python -m btst buy       # review and confirm before 3:30 PM
python -m btst exit      # next trading day, start at 9:15 AM and leave it running
python -m btst report
```

## Top gainers and losers (F&O only)

```bash
python -m btst movers            # ~3:00-3:10 PM IST; --top 20 is the default
```

Ranks all F&O stocks by today's % change (liquid ones only; stocks pinned at a circuit limit are skipped), then:

- **Top 20 gainers** go through the same calendar check, market and catalyst agents, and risk gate as `scan`. The result is **up to 10 BTST buys** (`MAX_POSITIONS`, default 10) that `python -m btst buy` can place. Each buy is `CAPITAL_PER_TRADE` (default 20,000), so ten buys can be 2,00,000 of exposure: lower either setting if that is too much.
- **Top 20 losers give up to 10 SELL ideas** (`MAX_SELL_IDEAS`, default 10) with a sell limit, a stop above and a target below. They are advisory: a cash BTST trade is long-only, so a sell is an intraday or stock-futures trade that this tool never places. The review rules mirror the buy side: results due, the F&O ban list or surveillance veto an idea; bad news supports it; good news is short-squeeze risk and skips it.

Biggest movers are often stretched, so `movers` is a different bet from `scan` (which also demands a strong close, volume surge and trend). Paper-trade both and compare in `python -m btst report`.

## Claude Code subagents (no API keys for the AI step)

Instead of calling the Gemini/Claude API from Python, you can let Claude Code run the AI steps. The repo ships project subagents in `.claude/agents/` and slash commands in `.claude/commands/`:

| Piece | What it does |
|---|---|
| `/btst-scan [scan\|movers]` | Screens in code, runs the two subagents in parallel, risk-gates in code, shows the plan. **Never runs `buy`.** |
| `btst-market-context` | Overnight-risk verdict (JSON). Web search only. |
| `btst-catalyst-analyst` | Per-stock news catalyst and veto (JSON). Web search only. |
| `/btst-morning` + `btst-morning-briefer` | 8:30 AM pre-market brief. Research only. |

The subagents have no shell access and cannot place orders. The hand-off is plain files: `python -m btst scan --screen-only` (or `movers --screen-only`) writes `data/shortlist-<date>.json`; the agents' JSON goes to `data/market-<date>.json` and `data/reviews-<date>.json`; `python -m btst plan --market ... --reviews ...` runs the same risk gate and writes the plan that `python -m btst buy` places after your confirmation.

### Using the Kite (Zerodha) MCP instead of Dhan

If the Kite MCP connector is connected to Claude Code (tools named `mcp__kite__*`), use these instead of the Dhan-based commands:

| Piece | What it does |
|---|---|
| `/btst-kite-scan [btst\|movers]` | Logs in to Kite, fetches live quotes for the whole universe in one call, saves them, runs `python -m btst kite-screen`, then the market and catalyst subagents, then the code risk gate. Needs no Dhan or AI API keys. Never places orders. |
| `/btst-kite-exit` + `btst-exit-manager` | Morning check: compares your Kite holdings and live prices with yesterday's planned stop and target and says sell now / sell at open / hold to 9:45. Read-only. |

Limits to know: the Kite screen uses only the live quote (move, close position, turnover, order book), not price history, so it is lighter than `scan`. Only the Kite read tools are listed for the exit agent, no order tools are used anywhere, and `python -m btst buy` refuses live orders for Kite-sourced plans (it would send Kite symbols to Dhan), so you place those in Kite yourself. If your Kite connector has a different name, the tool prefix changes: edit the `tools:` line in `.claude/agents/btst-exit-manager.md`.

## Results and bulk-deal calendar

The calendar applies to **every stock in `universe.txt`**, not just a few. Each `scan` first refreshes it from NSE's board-meeting and bulk/block-deal feeds (`--no-sync` skips this; if NSE is unreachable it falls back to the saved file), then checks it. `calendar.csv` (columns `symbol,type,date,note,source`) is checked on every `scan`:

- **`results` / `board_meeting` today or on the next trading day → the stock is dropped from the shortlist** (a code rule, not an agent judgement). An overnight hold through a result is a gap gamble.
- **`bulk_deal` / `block_deal` in the last 3 days → shown as a note only.** A big buy can support a stock and a big promoter or PE sale can weigh on it, so it is context, not a signal.

```bash
python -m btst calendar sync                      # refresh all stocks from NSE now (--days 45)
python -m btst calendar list --days 30            # upcoming events
python -m btst calendar check TCS                 # safe to hold overnight?
python -m btst calendar add INFY results 2026-10-23 --note "Q2 FY27" --source "company notice"
python -m btst calendar import nse_board_meetings.csv   # bulk load: symbol,type,date,note,source
```

A stock with **no results date on file** is not blocked, but the scan prints a warning so you can confirm it is not reporting tomorrow. The NSE feed reader was written against NSE's public JSON endpoints and is unit-tested with sample payloads; if NSE changes the format or blocks the request, use `calendar add` / `calendar import` instead.

Weekends are skipped when finding the "next trading day". Put NSE holidays (one `YYYY-MM-DD` per line) in `holidays.txt` next to the calendar. Dates seeded from news are marked "verify on NSE"; confirm them against the exchange's board-meeting and bulk-deal pages before relying on them.

## Notes and risks

- **Short delivery:** if your seller fails to deliver, your BTST sell becomes a short delivery and the exchange auctions it at a penalty. Stick to liquid stocks (`MIN_TURNOVER_CR`).
- **Gap-downs** can blow through the stop-loss. Keep position sizes small.
- In live mode, `exit` checks whether yesterday's buy actually filled before selling. Exit prices in the journal are the LTP when the exit fired, not the exact fill price.
- Costs such as STT (0.1% each side), DP charges, stamp duty and GST are not deducted in the journal P&L.

## Tests

```bash
pytest -q
```
