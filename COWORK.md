# Cowork setup for the BTST subagents

Research only. Nothing here places orders; you place any trade yourself. Not financial advice. The Cowork menu names below are from memory and may differ slightly.

## 1. Install the plugin
- Claude desktop app -> Cowork -> Customize (or Plugins).
- Upload `btst-agents.zip`, or add `https://github.com/bns218/BTST` as a source.
- Enable `btst-agents`. Four agents should appear: `btst-market-context`, `btst-catalyst-analyst`, `btst-morning-briefer`, `btst-exit-manager`.

## 2. Connect Kite
- Settings -> Connectors -> add Zerodha Kite and log in. Log in again each trading day.
- `btst-exit-manager` lists tools named `mcp__kite__*`. If your connector has a different name, edit its `tools:` line (in both `agents/` and `.claude/agents/`).

## 3. Working folder
Choose an empty folder such as `BTST-desk` in Cowork to hold the saved briefs and pick notes.

## 4. Scheduled tasks (weekdays, IST; they run only while your computer is on)

**8:29 AM**
> Use btst-morning-briefer for today's pre-market brief. Use Kite for yesterday's closing prices and F&O gainers and losers. Save the brief to the folder as brief-<date>.md.

**3:05 PM**
> Using Kite quotes, list today's top 20 NSE F&O gainers and top 20 losers. Run btst-market-context. Then run btst-catalyst-analyst on the gainers (side long) and on the losers (side short) and give me up to 10 buys and up to 10 sell ideas with stop -1% and target +2%. Do not place orders. Save the list to picks-<date>.md.

**4:15 PM**
> Use Kite to get today's closing prices for the picks in picks-<date>.md and tell me how many moved the right way, buys up and sells down. Save the result to review-<date>.md.

If Cowork cannot schedule tasks, paste these prompts by hand at those times.

## 5. Test
Run the 3:05 PM prompt once by hand. If the output says prices are unverified, Kite is not connected or not logged in.

## Limits
- There is no saved results calendar. The earnings-day check relies on web search, so confirm results dates on NSE before holding anything overnight.
- Sells are intraday or futures ideas only; a cash BTST position cannot be short overnight.
- Agents never place orders.
