# Watchdog-Apex.ps1 - Apex full autonomy layer
# 1. Boots the stack once at logon.
# 2. Forever after: verifies both Python surfaces (evolution loop + bridge) are
#    alive and restarts any that dies. No human needed. Ever.
[CmdletBinding()]
param()

$Root   = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$PyExe  = "$Root\apex_venv\Scripts\python.exe"
$Log    = "$Root\Logs\watchdog.log"

function Write-WdLog([string]$Msg) {
    $stamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    "$stamp [WATCHDOG] $Msg" | Out-File $Log -Append -Encoding utf8
    Write-Host "[$stamp] $Msg"
}

# Single-instance guard: exclusive file lock. The OS releases it the instant
# the owning process dies, so stale or crashed watchdogs can NEVER block a
# healthy replacement (unlike named-mutex tricks which fail across session
# contexts). If another Apex watchdog is running, this instance exits.
try {
    $LockStream = [System.IO.File]::Open("$Root\watchdog.lock", 'OpenOrCreate', 'ReadWrite', 'None')
} catch [System.IO.IOException] {
    Write-WdLog "Another Apex watchdog owns watchdog.lock. Exiting cleanly (no dupe)."
    exit 0
}
Write-WdLog "Watchdog acquired watchdog.lock - sole authority."

function Get-ApexProcess([string]$ScriptName) {
    # psutil-based check via proc_check.py - WMI/CIM proved hang-prone under
    # zombie churn and is no longer trusted anywhere in the supervision stack.
    $r = Start-Process $PyExe -ArgumentList "`"$Root\Scripts\proc_check.py`" check `"$ScriptName`"" -Wait -PassThru -NoNewWindow
    if ($r.ExitCode -eq 0) { return "alive" }
    return $null
}

function Start-Apex([string]$ScriptName, [int]$Port) {
    # PORT REACHABILITY IS THE SOURCE OF TRUTH. A python process "existing"
    # means nothing if it stopped serving its port - that is a hung zombie.
    $t = New-Object System.Net.Sockets.TcpClient
    $portUp = $false
    try { $t.Connect("127.0.0.1", $Port); $portUp = $true } catch {} finally { $t.Dispose() }
    if ($portUp) { return $true }

    # Port down: if a python process still matches, it is a stuck zombie.
    $proc = Get-ApexProcess $ScriptName
    if ($proc) {
        Write-WdLog "HUNG ZOMBIE for $ScriptName (port $Port down, process alive). Killing..."
        $kill = Start-Process $PyExe -ArgumentList "`"$Root\Scripts\proc_check.py`" kill `"$ScriptName`"" -Wait -PassThru -NoNewWindow
        Start-Sleep -Seconds 1
    }

    Write-WdLog "Pulse lost for $ScriptName (port $Port). Resurrecting..."
    Start-Process $PyExe -ArgumentList "`"$Root\$ScriptName`"" -WorkingDirectory $Root -WindowStyle Hidden
    Start-Sleep -Seconds 5
    $t2 = New-Object System.Net.Sockets.TcpClient
    try { $t2.Connect("127.0.0.1", $Port); $t2.Close(); return $true } catch { return $false } finally { $t2.Dispose() }
}

# --- First breath: run the standard boot sequence ONCE, asynchronously ---
# The watchdog must never block inside boot (e.g., a stalled pip fetch would
# freeze the whole supervision loop). Boot runs detached; port-guards make it idempotent.
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Root\Boot-ApexShort.ps1`"" -WindowStyle Hidden
Start-Sleep -Seconds 10

# --- Eternal watch ---
Write-WdLog "Watchdog active. Polling every 60 seconds."
while ($true) {
    try {
        Start-Apex "run_apex_evolution.py" 8080 | Out-Null
        Start-Apex "optimized_agent.py"    8081 | Out-Null
    } catch {
        Write-WdLog "Watch cycle error: $_"
    }
    # Jittered poll: keeps two watchdogs from ever polling the same instant,
    # even in the rare case the single-instance mutex is bypassed.
    Start-Sleep -Seconds (Get-Random -Minimum 55 -Maximum 70)
}
