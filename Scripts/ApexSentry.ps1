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
# (the 2026-11-04 fix: this ran EVERY 1-min tick - pure process churn; now a
# 30-min cooldown receipt, mirroring the idle-gym pattern.)
$syncPath = 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexPackSync.py'
$syncCd = "$root\Logs\pack_sync_cooldown.txt"
$syncDo = $true
if (Test-Path $syncCd) {
    try { $lastSync = Get-Content $syncCd -First 1; if (($now2 = Get-Date) - [datetime]$lastSync -lt [timespan]::FromMinutes(30)) { $syncDo = $false } } catch {}
}
if ($syncDo) {
    if (Test-Path $syncPath) {
        Start-Process "$root\apex_venv\Scripts\python.exe" -ArgumentList $syncPath -WindowStyle Hidden
        "$((Get-Date).ToString('s')) sentry: pack sync tick (30-min cadence)" |
            Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
        [System.IO.File]::WriteAllText($syncCd, (Get-Date).ToString('s'))
    }
}

# THE WARM BRAIN (2026-11-04): keep the floor brains resident on free RAM.
# 4-h cooldown + its own RAM gate inside (WarmBrain.py prints honestly).
$warmCd = "$root\Logs\warm_brain_cooldown.txt"
$warmDo = $true
if (Test-Path $warmCd) {
    try { $lastWarm = Get-Content $warmCd -First 1; if (((Get-Date) - [datetime]$lastWarm).TotalHours -lt 4) { $warmDo = $false } } catch {}
}
if ($warmDo) {
    Start-Process "$root\apex_venv\Scripts\python.exe" -ArgumentList (Join-Path $root 'Scripts\WarmBrain.py') -WindowStyle Hidden
    [System.IO.File]::WriteAllText($warmCd, (Get-Date).ToString('s'))
    "$((Get-Date).ToString('s')) sentry: warm-brain beat" | Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}

# Guard Apex's ears (wake-word listener) if killed - NOT every minute (the
# respawn-storm fix: a 5-min cooldown receipt; the CIM check is kept only as
# the cheap existence probe, the watchdog remains process-truth authority).
$ears = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*ApexEars.ps1*' }
$earsCd = "$root\Logs\ears_cooldown.txt"
$earsDo = $true
if (Test-Path $earsCd) {
    try { $lastEars = Get-Content $earsCd -First 1; if (((Get-Date) - [datetime]$lastEars).TotalMinutes -lt 5) { $earsDo = $false } } catch {}
}
if (-not $ears -and $earsDo) {
    Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\Scripts\ApexEars.ps1")
    [System.IO.File]::WriteAllText($earsCd, (Get-Date).ToString('s'))
    "$((Get-Date).ToString('s')) sentry: apex ears missing -> ApexEars.ps1 (re)started (5-min cooldown armed)" |
        Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
}


# Idle-driven autonomy: micro gym/farm rounds when RAM is healthy + cooldown 2h.
# (The TRIPWIRE rides here too: the integration hooks' manifest check - the
# silent-revert class dies on a 1-min cadence, 30-min cooldown in the organ.)
& "$root\apex_venv\Scripts\python.exe" "$root\Scripts\HookCheck.py" 2>$null | Where-Object { $_ -like '*tripwire*' } | Out-File "$root\Logs\sentry.log" -Append -Encoding utf8
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
