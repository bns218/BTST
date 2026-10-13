---
description: Pre-market (8:30 AM IST) brief with the btst-morning-briefer subagent. Research only.
---

Work from the repo root and activate `.venv` if it exists. Gather context with read-only commands: `TZ=Asia/Kolkata date`, `python -m btst calendar list --days 3`, and `python -m btst report` (skip the report if there is no journal yet). Launch the `btst-morning-briefer` subagent, pass it that output, and show the user its brief unchanged. Never run `python -m btst buy` or `exit`, never place orders, never use trading tools.
