# Registers the 3 daily BTST cycles in Windows Task Scheduler, Monday-Friday only.
# Each task runs Claude Code headless (`claude -p`) inside this repo so the
# subagents in .claude/agents can read and write the repo files.
#
# Requirements: Claude Code CLI installed and logged in (`claude` on PATH),
# with the Kite MCP server added (e.g. `claude mcp add --transport http kite https://mcp.kite.trade/mcp`).
# Usage (normal PowerShell, from the repo root):  .\scripts\setup_windows_scheduler.ps1
# Remove:  Get-ScheduledTask -TaskName "BTST*" | Unregister-ScheduledTask -Confirm:$false
#
# Note: the PC's clock must be set to India Standard Time, and the PC must be awake at these times.

param(
    [string]$RepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) { Write-Error "Claude Code CLI ('claude') not found on PATH."; exit 1 }

$weekdays = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

$cycles = @(
    @{ Name = "BTST 1 - 8.45AM Morning Exit Plan"; At = "8:45AM";
       Prompt = "Run the btst-morning-845am subagent as defined in .claude/agents/2-btst-morning-845am.md. Load the latest data/picks-<previous trading day>.json, audit GIFT Nifty, global cues, overnight news and today's F&O ban list, and save data/brief-<today>.md. Research only; never place orders." },
    @{ Name = "BTST 2 - 3.15PM Screener"; At = "3:15PM";
       Prompt = "Run the btst-market-shield subagent (.claude/agents/4-btst-market-shield.md), then the btst-screener-315pm subagent (.claude/agents/1-btst-screener-315pm.md) using the shield verdict. Read review/lessons.md first. Save data/picks-<today>.json before 3:30 PM IST. Research only; never place orders." },
    @{ Name = "BTST 3 - 3.45PM Learner"; At = "3:45PM";
       Prompt = "Run the btst-learner-345pm subagent as defined in .claude/agents/3-btst-learner-345pm.md. Review the previous trading day's picks with Kite minute candles, update review/review-log.json and review/lessons.md, and save review/review-<today>.md. Research only; never place orders." }
)

foreach ($c in $cycles) {
    $escaped = $c.Prompt.Replace('"', '\"')
    $action  = New-ScheduledTaskAction -Execute $claude -Argument "-p `"$escaped`"" -WorkingDirectory $RepoPath
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $weekdays -At $c.At
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Minutes 40)
    Register-ScheduledTask -TaskName $c.Name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "Registered '$($c.Name)' at $($c.At), Monday-Friday" -ForegroundColor Green
}

Write-Host "Done. NSE holidays are not skipped automatically; each agent checks the trading calendar and exits on holidays." -ForegroundColor Yellow
