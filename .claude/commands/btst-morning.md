---
description: Pre-market (8:30 AM IST) brief with the btst-morning-briefer subagent. Research only.
---

Work from the repo root and activate `.venv` if it exists. Gather context with read-only commands: `TZ=Asia/Kolkata date`, `python -m btst calendar list --days 3`, and the newest plan file if any (`ls -t data/plan-*.json | head -1`). Launch the `btst-morning-briefer` subagent, pass it that output (plan file path included), and show the user its brief unchanged. Never place orders, never use trading tools.
