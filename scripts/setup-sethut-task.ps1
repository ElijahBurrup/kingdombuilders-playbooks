# setup-sethut-task.ps1
# Run this ONCE (as Administrator) to:
#   1. Register a scheduled task that runs every 30 minutes
#   2. Create a desktop shortcut for manual runs
#
# The task launches Claude with the full prompt chain and runs SetHut
# to generate a new Kingdom Builders playbook.
#
# Usage: Run as Administrator
#   powershell -ExecutionPolicy Bypass -File "C:\Projects\KingdomBuilders.AI\scripts\setup-sethut-task.ps1"

# --- Check for Administrator ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator, then re-run this script."
    exit 1
}

$Python     = "C:\Users\elija\AppData\Local\Programs\Python\Python313\pythonw.exe"
$ScriptPath = "C:\Projects\KingdomBuilders.AI\scripts\sethut_launcher.py"
$TaskName   = "KingdomBuilders-SetHut"
$Desktop    = [Environment]::GetFolderPath("Desktop")

# --- 1. Scheduled Task (every 30 minutes) ---
Write-Host "`n=== Registering SetHut Scheduled Task ===" -ForegroundColor Cyan

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task."
}

$action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory "C:\Projects\KingdomBuilders.AI"

# Daily trigger at midnight, repeating every 30 minutes indefinitely
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00AM"
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "12:00AM" `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration ([TimeSpan]::MaxValue)).Repetition

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Every 30 min: Launch Claude to generate a new Kingdom Builders playbook (SetHut)" `
    -RunLevel Highest | Out-Null

Write-Host "Task '$TaskName' registered (every 30 minutes)." -ForegroundColor Green

# --- 2. Desktop Shortcut (manual run) ---
Write-Host "`n=== Creating Desktop Shortcut ===" -ForegroundColor Cyan

$shortcutPath = Join-Path $Desktop "SetHut Launcher.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "C:\Users\elija\AppData\Local\Programs\Python\Python313\python.exe"
$shortcut.Arguments = "`"$ScriptPath`""
$shortcut.WorkingDirectory = "C:\Projects\KingdomBuilders.AI"
$shortcut.Description = "Manually launch Claude SetHut to generate a new playbook"
$shortcut.IconLocation = "shell32.dll,137"
$shortcut.Save()

Write-Host "Desktop shortcut created: $shortcutPath" -ForegroundColor Green

# --- 3. Verification ---
Write-Host "`n=== Verification ===" -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "  $TaskName - $($task.State)" -ForegroundColor Green
} else {
    Write-Host "  $TaskName - NOT FOUND" -ForegroundColor Red
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Task:     $TaskName (every 30 minutes)" -ForegroundColor DarkGray
Write-Host "  Script:   $ScriptPath" -ForegroundColor DarkGray
Write-Host "  Log:      S:\My Drive\1. Projects\Tools\logs\sethut_launcher.log" -ForegroundColor DarkGray
Write-Host "  Shortcut: $shortcutPath" -ForegroundColor DarkGray
