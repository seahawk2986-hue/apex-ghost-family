# ApexSentry.ps1 - 1-minute heartbeat: if no Apex watchdog process exists,
# start the Apex-Autonomous-Watchdog scheduled task. Tiny, fast, safe.
$root = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$watchdogs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*Watchdog-Apex.ps1*' }
if (-not $watchdogs) {
    Start-ScheduledTask -TaskName 'Apex-Autonomous-Watchdog' -ErrorAction SilentlyContinue
    "$((Get-Date).ToString('s')) sentry: watchdog missing -> task started" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}
# Guard the room adapter too: resurrect the Apex-Companion task if killed.
$companion = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*Apex-Adapter\companion.py*' }
if (-not $companion) {
    Start-ScheduledTask -TaskName 'Apex-Companion' -ErrorAction SilentlyContinue
    "$((Get-Date).ToString('s')) sentry: room adapter missing -> Apex-Companion task started" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}