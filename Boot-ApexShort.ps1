function Write-Log { param([string]$Msg, [string]$Col = "White"); $T = Get-Date -Format "HH:mm:ss"; Write-Host "[$T] $Msg" -ForegroundColor $Col }

$Root = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
Set-Location $Root

# Idempotency guard: never spawn a layer that is already listening.
function Test-ApexPort([int]$Port) {
    $t = New-Object System.Net.Sockets.TcpClient
    try { $t.Connect('127.0.0.1', $Port); return $true } catch { return $false }
    finally { $t.Dispose() }
}

function Test-ApexProcess([string]$ScriptName) {
    # psutil-based via proc_check.py (WMI-free)
    $r = Start-Process $PyExe -ArgumentList "`"$Root\Scripts\proc_check.py`" check `"$ScriptName`"" -Wait -PassThru -NoNewWindow
    return $r.ExitCode -eq 0
}

try {
    Write-Log "==========================================================" "Cyan"
    Write-Log "     APEX AUTONOMOUS DEVELOPMENT GATEWAY (8GB OPTIMIZED) " "Cyan"
    Write-Log "==========================================================" "Cyan"

    # --- 1. Local model servers -------------------------------------------------
    $PyExe = "$Root\apex_venv\Scripts\python.exe"

    $OllamaCheck = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if (-not $OllamaCheck) {
        Write-Log "[!] Ollama offline. Launching background instance..." "Yellow"
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }
    if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -InformationAction SilentlyContinue -WarningAction SilentlyContinue).TcpTestSucceeded) {
        Write-Log "[OK] Ollama server online (port 11434)." "Green"
    } else {
        Write-Log "[!] Ollama still unreachable on port 11434." "Red"
    }

    if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 1234 -InformationAction SilentlyContinue -WarningAction SilentlyContinue).TcpTestSucceeded) {
        Write-Log "[OK] LM Studio server online (port 1234)." "Green"
    } else {
        Write-Log "[!] LM Studio not reachable on port 1234. Start it and load deepseek-r1-distill-llama-8b + qwen2.5-coder-7b-instruct." "Red"
    }

    # --- 2. Interpreter sanity check --------------------------------------------
    if (Test-Path $PyExe) {
        & $PyExe --version 2>&1 | ForEach-Object { Write-Log "[OK] Python runtime: $_" "Green" }
    } else {
        throw "apex_venv python not found at $PyExe. Run: py -3.14 -m venv $Root\apex_venv"
    }

    # --- 3. Fast dependency sync (no network when already installed) -----------
    $depOk = & $PyExe -c "import fastapi, uvicorn, pydantic, requests, bs4, dotenv, psutil, httpx; print('OK')" 2>&1
    if ("$depOk" -match 'OK') {
        Write-Log "[OK] Dependencies satisfied (import check)." "Green"
    } else {
        Write-Log "[*] Dependency import failed - running pip once: $depOk" "Yellow"
        $pipProc = Start-Process $PyExe -ArgumentList "-m pip install -q -r `"$Root\requirements.txt`"" -Wait -PassThru -NoNewWindow
        if ($pipProc.ExitCode -eq 0) { Write-Log "[OK] pip sync completed." "Green" } else { Write-Log "[!] pip sync failed (code $($pipProc.ExitCode))" "Yellow" }
    }

    # --- 4. Logs directory -------------------------------------------------------
    $LogsDir = "$Root\Logs"
    if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir | Out-Null; Write-Log "[OK] Logs directory created." "Green" }

    # --- 4.5 Config lint: fail LOUDLY if the brain's configs are corrupt ---------
    foreach ($cf in @('HostGuard.json', 'ApexSelf.json', 'PeerProfiles.json', 'layer_pids.json', 'RewardLedger.json')) {
        $p = Join-Path $Root "Config\$cf"
        if (Test-Path $p) {
            try {
                $null = Get-Content $p -Raw | ConvertFrom-Json
                Write-Log "[OK] Config lint: $cf valid." "Green"
            } catch {
                Write-Log "[!] Config lint FAILED: $cf is corrupt - rename to .corrupt and restore from CheckpointState.json" "Red"
            }
        }
    }

    # --- 5. Launch the two application layers ------------------------------------
    # Spawn authority: if the watchdog lock exists, the watchdog already
    # supervises/respawns these layers - boot MUST NOT spawn (race source).
    # Boot only spawns when running standalone (no watchdog active).
    $WatchdogActive = Test-Path "$Root\watchdog.lock"

    if ((Test-Path "$Root\run_apex_evolution.py") -and (-not (Test-ApexPort 8080)) -and (-not (Test-ApexProcess 'run_apex_evolution.py')) -and (-not $WatchdogActive)) {
        Write-Log "[*] Igniting self-directed evolution loop (port 8080)..." "Cyan"
        Start-Process $PyExe -ArgumentList "`"$Root\run_apex_evolution.py`"" -WorkingDirectory $Root -WindowStyle Hidden
    } elseif ($WatchdogActive) {
        Write-Log "[OK] Watchdog owns process supervision - boot stays out of spawning." "Green"
    } else {
        Write-Log "[OK] Evolution loop already alive (port 8080) - not duplicating." "Green"
    }
    if ((Test-Path "$Root\optimized_agent.py") -and (-not (Test-ApexPort 8081)) -and (-not (Test-ApexProcess 'optimized_agent.py')) -and (-not $WatchdogActive)) {
        Write-Log "[*] Starting inbound network bridge (port 8081)..." "Cyan"
        Start-Process $PyExe -ArgumentList "`"$Root\optimized_agent.py`"" -WorkingDirectory $Root -WindowStyle Hidden
    } elseif ($WatchdogActive) {
        Write-Log "[OK] Bridge supervision owned by watchdog (port 8081)." "Green"
    } else {
        Write-Log "[OK] Network bridge already alive (port 8081) - not duplicating." "Green"
    }

    # --- 6. Hardware health ------------------------------------------------------
    $MemoryUsage = Get-Counter "\Memory\Available MBytes" -ErrorAction SilentlyContinue
    if ($MemoryUsage) {
        $AvailMB = [math]::Round($MemoryUsage.CounterSamples[0].CookedValue)
        if ($AvailMB -lt 2048) {
            Write-Log "[!] Only ${AvailMB}MB RAM free - close heavy apps before heavy evolution cycles." "Yellow"
        } else {
            Write-Log "[OK] Hardware headroom OK (${AvailMB}MB free RAM)." "Green"
        }
    }

    Write-Log "Apex gateway initialized. Logs: $LogsDir" "Cyan"
} catch {
    Write-Log "[CRITICAL ALERT] Boot failed: $_" "Red"
}
