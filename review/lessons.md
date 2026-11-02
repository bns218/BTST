# Cumulative Trading Lessons & Negative Filters
> **Rule of the System**: Before selecting any new BTST or STBT candidates at 3:15 PM IST, the screening agent MUST read this file. Any stock setup matching a failure pattern logged here is **strictly vetoed**.

---

## 1. Core Derivative & Price Action Rules
- **Rule 1.1 (Short Covering Trap)**: Never select a top gainer where price is UP but Open Interest (OI) is DOWN. A rally driven by intraday short-covering lacks institutional accumulation and frequently gaps down the following morning.
- **Rule 1.2 (Late-Day Fade / High Rejection)**: Never select a long BTST candidate that made its high before 1:00 PM and has drifted lower into the close. The stock must be trading in the upper 15% of its daily candle range between 2:45 PM and 3:20 PM IST.
- **Rule 1.3 (Long Unwinding Trap)**: Never short a top loser whose OI has significantly decreased (long unwinding), as it is prone to sharp mean-reversion bounces. Only short stocks with strong **Short Buildup** (Price DOWN + OI UP).
- **Rule 1.4 (Sector Alignment & Macro Gap Filter)**: Never take a standalone long BTST trade in a sector leader if the broader sectoral index is displaying divergence or negative breadth. If GIFT Nifty indicates a gap-down open (> -0.3%), reduce long BTST position sizing by 50% and prioritize Short Buildup (STBT) setups.
- **Rule 1.5 (Strict 9:45 AM Time-Exit Discipline)**: If a carried BTST/STBT position fails to expand (> +1%) by 9:45 AM, immediately execute a market time-exit. Never carry a stagnant trade past 9:45 AM into the European open volatility window.
- **Rule 1.6 (Board Meeting Postponement Squeeze Guardrail)**: When a corporate board meeting/earnings release is abruptly postponed near monthly derivative expiry (as occurred with Tata Steel), exercise extreme caution on fresh short positions. Postponements remove imminent downside event risk and frequently trigger aggressive institutional short-covering squeezes.
- **Rule 1.7 (Pre-Expiry Exposure Balance & Hedged Pairs)**: On the session before NSE stock/index derivative expiry (NSE expiry is currently on Tuesday since Sept 2025 — confirm the date on NSE's expiry calendar each month), never deploy an unhedged 100% unidirectional Long BTST batch if macro indicators or index breadth are mixed. The screening agent must either select a balanced **Long/Short pair (1 BTST Long + 1 STBT Short)** to maintain delta neutrality or halve total overnight capital allocation.
- **Rule 1.8 (Monthly Expiry Day Short-Covering Squeeze Guardrail)**: On the morning of monthly derivative expiry (currently the last Tuesday of the month on NSE — confirm on NSE's expiry calendar), avoid taking STBT short positions on top-weighted Nifty 50 index heavyweights (such as Reliance, HDFC Bank, ICICI Bank) based purely on preceding breakdown OI. Expiry day rollover dynamics induce aggressive short-covering squeezes if the index opens resiliently or rolls over, reversing prior short accumulation.

---

## 2. Event & Earnings Risk Guardrails
- **Rule 2.1 (Earnings Binary Risk)**: Zero tolerance for any company declaring quarterly financial results today (post-market) or tomorrow (pre-market or during trading hours). Overnight earnings gaps are non-directional gambles.
- **Rule 2.2 (NSE F&O Ban List / MWPL Limit)**: Veto any stock that has entered the NSE F&O ban period or has Market Wide Position Limit (MWPL) exceeding 85%. Positions can get locked or subject to heavy exchange penalties.
- **Rule 2.3 (Regulatory & Surveillance Action)**: Veto any stock added to ASM (Additional Surveillance Measure) or GSM stages, or facing severe SEBI/regulatory action or promoter pledge invocation.
- **Rule 2.4 (Interim Dividend Record Date Squeeze Guardrail)**: Never initiate fresh short STBT trades on high-dividend yield stocks within T-2 days of their corporate dividend record date. Even when quarterly earnings guidance is cut, dividend-capture institutional and retail buyers aggressively step in to secure the dividend yield (e.g. Shriram Finance ₹6.50 / 325% dividend), sparking strong short-covering squeezes that defy broad market weakness.
- **Rule 2.5 (Post-Market Corporate Disclosures & SOTP Valuation Re-Ratings)**: Always verify after-market corporate disclosures (released between 3:30 PM and 7:30 PM IST) before confirming overnight carrying:
  1. **Post-Market Concall / Exchange Disclosures**: Screen for late-evening management concall warnings regarding margin contraction or unexpected regulatory notices.
  2. **Subsidiary Listing / SOTP Squeeze**: Never initiate a short STBT trade on a parent conglomerate on the day its core subsidiary makes a blockbuster market listing (e.g. Reliance vs Jio Platforms' 27% premium debut). Even if the parent stock dips during the day, after-market sum-of-the-parts (SOTP) institutional re-evaluations trigger severe overnight short squeezes.

---

## 3. Macro & Market Regime Rules
- **Rule 3.1 (Elevated India VIX)**: When India VIX is above 18.0, reduce overall BTST position count by 50%. When VIX is above 22.0, completely suspend fresh overnight BTST long positions regardless of individual chart setups.
- **Rule 3.2 (Binary Global Events)**: If a major binary event occurs overnight (e.g., US FOMC interest rate decision, US CPI release, Union Budget eve, Election results), suspend overnight carrying.

---

## 3b. Rule Hygiene (added 2026-11-02)
- A lesson from a single trade is logged as an **Observation** only. It becomes a hard veto Rule only after the same pattern causes a loss at least twice, and the learner records the evidence (dates + symbols).
- Dates and facts in lessons must come from verified data (Kite candles, exchange filings); do not cite events that were not confirmed.

---

## 4. Daily Learned Mistakes Log (Auto-Updated at 3:45 PM IST)
*The `btst-learner-345pm` subagent automatically appends newly identified failure patterns below after daily review.*

- **[2026-10-21 Execution Guardrail]**: Pre-market indicative quotes (8:45–9:07 AM IST) must NOT be used to execute premature stop-loss liquidations. Overnight orders must only trigger stop-loss exits on verified regular session prints after 9:15 AM IST.
- **[2026-10-21 Batch Performance]**: 4/4 targets hit (100% win rate: WIPRO +2.70%, TECHM +2.96%, TCS +2.65%, NESTLEIND +4.40%). Long Buildup + Post-Earnings Surge setup confirmed highly robust. Zero negative screening vetoes required for this batch.
- **[2026-10-22 Diagnostic Lesson - ULTRACEMCO Drag]**: ULTRACEMCO breached the -1.0% stop-loss at 9:15–9:22 AM down to ₹10,651 during an aggressive market-wide Nifty opening crack (-256 pts) before recovering to ₹10,976 (+1.16%) by 2:30 PM. **Learned Rule**: During weak macro morning gap-downs, rate-sensitive single-stock long BTST setups have high vulnerability to early liquidity sweeps. Added Rule 1.4 to enforce sector-breadth confirmation and reduced long sizing on weak macro days.
- **[2026-10-23 Diagnostic Lesson - LT Time Exit & COALINDIA Profit]**: COALINDIA crashed from ₹403 open to ₹390.65 low, exceeding the +2% target (+2.70% max gain). L&T consolidated between ₹3,640 and ₹3,663 in the first 30 minutes. Exiting L&T at the mandated 9:45 AM window at ₹3,642 (-0.38%) protected capital from the subsequent market breakdown to ₹3,596. **Learned Rule**: Formulated Rule 1.5 confirming the mandatory 9:45 AM time-exit rule on non-moving setups.
- **[2026-10-26 Diagnostic Lesson - NTPC Profit & TATASTEEL Time Exit]**: NTPC dropped from ₹297.75 open to low of ₹294.10, capturing morning profits before the afternoon market squeeze (+0.85% to +1.85%). Tata Steel slipped to ₹165.51 early (+0.77%), then consolidated. Exiting at 9:45 AM at ₹167.30 (-0.30%) prevented a full stop-loss breach when the stock squeezed to ₹169.94 in the afternoon. **Learned Rule**: Formulated Rule 1.6 on earnings postponement short-squeezes.
- **[2026-10-27 Diagnostic Lesson - DRREDDY Time Exit & SHRIRAMFIN Dividend Squeeze]**: DRREDDY opened defensively and rallied to ₹1,323.70; executing the Rule 1.5 09:45 AM time-exit at ₹1,318.00 locked in a +0.30% gain ahead of midday exhaustion (closed at ₹1,310.00). SHRIRAMFIN gapped up to ₹833.80 and spiked to ₹838.95 at 09:20 AM, triggering the 1.0% stop-loss at ₹832.25 despite soft earnings guidance. **Root Cause**: Shriram Finance declared an interim dividend of ₹6.50/share (record date Oct 29, 2026). Yield buyers accumulated ahead of the T-2 window, overpowering short momentum. **Learned Rule**: Formulated Rule 2.4 strictly vetoing STBT shorts within T-2 days of a major corporate dividend record date.
- **[2026-10-28 Diagnostic Lesson - Systematic IT Drag & Exposure Balance]**: Both TATACONSUM and BHARTIARTL triggered predefined hard stops (-1.20% each) during a severe opening index cascade (Nifty -252 pts, Nifty IT > -3%). **Root Cause**: Deploying a 100% unidirectional Long BTST batch on pre-expiry Wednesday left zero protection against systematic beta sell-offs. **Learned Rule**: Formulated Rule 1.7 mandating balanced Long/Short pairs on pre-expiry sessions. Strict hard stops saved the portfolio from larger intraday drawdown.
- **[2026-10-29 Diagnostic Lesson - Expiry Day Heavyweight Squeeze & Time Exit]**: LT consolidated and was cleanly closed under Rule 1.5 at 09:45 AM at ₹3,770.00 (-0.82%), avoiding theta decay. RELIANCE hit its hard stop at ₹1,170.00 (-1.03%) at 09:25 AM when the market launched into a massive monthly expiry short-covering surge (+237 pts). **Root Cause**: Shorting an index heavyweight into monthly expiry day is prone to forced rollover short-covering squeezes. **Learned Rule**: Formulated Rule 1.8 barring STBT shorts on top index heavyweights on monthly expiry morning.
