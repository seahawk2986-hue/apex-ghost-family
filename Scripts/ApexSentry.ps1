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
# Guard Apex's room watcher (autonomous self-healing).
$rw = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*room_watcher2*' }
if (-not $rw) {
    Start-Process "$root\apex_venv\Scripts\pythonw.exe" -ArgumentList 'C:\Users\seaha\Apex-Adapter\room_watcher2.py' -WindowStyle Hidden
    "$((Get-Date).ToString('s')) sentry: room watcher missing -> relaunched" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}
# Autonomous pack maintenance: drift-only rebuild of deliverable packs.
$syncPath = 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexPackSync.py'
if (Test-Path $syncPath) {
    Start-Process "$root\apex_venv\Scripts\python.exe" -ArgumentList $syncPath -WindowStyle Hidden
    "$((Get-Date).ToString('s')) sentry: pack sync tick" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}

# Guard Apex's ears (wake-word listener) if killed.
$ears = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*ApexEars.ps1*' }
if (-not $ears) {
    Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\Scripts\ApexEars.ps1")
    "$((Get-Date).ToString('s')) sentry: apex ears missing -> ApexEars.ps1 (re)started" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}


# Idle-driven autonomy: micro gym/farm rounds when RAM is healthy + cooldown 2h.
$cdFile = "$root\Logs\idle_autonomy_cooldown.txt"
$now = Get-Date
$doIt = $true
if (Test-Path $cdFile) {
    try { $last = Get-Content $cdFile -First 1; if (($now - [datetime]$last).TotalHours -lt 2) { $doIt = $false } } catch {}
}
if ($doIt) {
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
        if ($freeGB -gt 6) {
            $pathChoice = if ((Get-Random -Max 2) -eq 0) { 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexGym.py' } else { 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\SeekGrowth.py' }
            $args2 = if ($pathChoice -like '*ApexGym*') { @($pathChoice, '--minutes', '5', '--traits', 'auto') } else { @($pathChoice, '--minutes', '5') }
            Start-Process "$root\apex_venv\Scripts\python.exe" -ArgumentList $args2 -WindowStyle Hidden
            [System.IO.File]::WriteAllText($cdFile, $now.ToString('s'))
            "$((Get-Date).ToString('s')) sentry: idle micro-session (RAM $freeGB GB free, runner: $pathChoice)" |
                Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
        }
    } catch {
        "$((Get-Date).ToString('s')) sentry: idle-autonomy failed: " + $_.Exception.Message |
            Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
    }
}
