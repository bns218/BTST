# BTST

AI-assisted **Buy Today, Sell Tomorrow** trading for NSE equities, using **Dhan** for market data and orders and **Claude** agents for news and risk judgement.

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
| `agents.py` → market context | Claude + web search | Checks global cues, GIFT Nifty, VIX, FII flows and event risk. Can block all new trades for the day |
| `agents.py` → catalyst | Claude + web search | Finds why each stock moved. Vetoes stocks with results tomorrow, regulatory action, pledges, or ASM/T2T moves |
| `risk.py` | Code | Ranks, sizes and sets SL/target, and enforces max positions, capital per trade, available funds and daily loss limit. **Agents can only remove trades, never add or resize them.** |
| `journal.py` | SQLite | Every trade, fill and exit, for review and tuning |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, ANTHROPIC_API_KEY
```

The Dhan access token comes from web.dhan.co → My Profile → Access DhanHQ APIs. Edit `universe.txt` to change which stocks are scanned.

## Daily use

```bash
python -m btst scan      # ~3:00-3:10 PM IST
python -m btst buy       # review and confirm before 3:30 PM
python -m btst exit      # next trading day, start at 9:15 AM and leave it running
python -m btst report
```

## Notes and risks

- **Short delivery:** if your seller fails to deliver, your BTST sell becomes a short delivery and the exchange auctions it at a penalty. Stick to liquid stocks (`MIN_TURNOVER_CR`).
- **Gap-downs** can blow through the stop-loss. Keep position sizes small.
- In live mode, `exit` checks whether yesterday's buy actually filled before selling. Exit prices in the journal are the LTP when the exit fired, not the exact fill price.
- Costs such as STT (0.1% each side), DP charges, stamp duty and GST are not deducted in the journal P&L.

## Tests

```bash
pytest -q
```
