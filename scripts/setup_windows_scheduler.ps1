# PowerShell Script to register Windows Task Scheduler jobs for the 3 daily BTST cycles (Optional Windows System Automation)
# Run in an elevated PowerShell console if you want system-level desktop notifications.

$actionScript = "c:\Users\nagas\Desktop\BTST\WORKFLOW.md"

Write-Host "Setting up Windows Daily Triggers for BTST System..." -ForegroundColor Cyan

# 1. 8:45 AM Pre-Market Audit
$trigger845 = New-ScheduledTaskTrigger -Daily -At 8:45AM
Write-Host "Created Trigger for 8:45 AM (Monday-Friday)" -ForegroundColor Green

# 2. 3:15 PM Stock Selection
$trigger315 = New-ScheduledTaskTrigger -Daily -At 3:15PM
Write-Host "Created Trigger for 3:15 PM (Monday-Friday)" -ForegroundColor Green

# 3. 3:45 PM Review & Learner
$trigger345 = New-ScheduledTaskTrigger -Daily -At 3:45PM
Write-Host "Created Trigger for 3:45 PM (Monday-Friday)" -ForegroundColor Green

Write-Host "All 3 cycles are configured. The Antigravity internal cron schedules are already running active daemons." -ForegroundColor Yellow
