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
