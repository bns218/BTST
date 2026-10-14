# BTST Claude Code subagents

Four research-only Claude Code subagents for NSE F&O BTST (buy today, sell tomorrow) work, in `.claude/agents/`:

| Subagent | Job |
|---|---|
| `btst-market-context` | Overnight-risk verdict for new long positions (web search only) |
| `btst-catalyst-analyst` | Per-stock news catalyst and event-risk veto, buy or sell side (web search only) |
| `btst-morning-briefer` | 8:30 AM pre-market brief |
| `btst-exit-manager` | Morning exit advice for yesterday's buys (read-only Kite MCP) |

They never place orders. Not financial advice.
