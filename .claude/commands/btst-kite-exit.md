---
description: Morning exit check for yesterday's BTST buys using the Kite MCP (read-only). Never places orders.
---

Work from the repo root. Find the most recent plan file with `ls -t data/plan-*.json | head -1` (stop and say so if there is none). Make sure the Kite session is logged in (`mcp__kite__get_profile`; if not, `mcp__kite__login` and wait for the user). Launch the `btst-exit-manager` subagent with that plan path and the current IST time (`TZ=Asia/Kolkata date`), and show the user its table unchanged. NEVER place, modify or cancel an order or use any Kite order tool; the user sells in Kite themselves.
