# ApexServe.ps1 - frontier inference serving profiles for our hardware
# RTX 3050 8GB | 16GB RAM | i5-10400F (6C/12T AVX2)
# Profiles:
#   Chat      : pin qwen3-8b as the ONLY resident chat brain + speculative draft
#   Code      : pin qwen2.5-14b-instruct (coding brain) + speculative draft
#   MoE       : DIY llama-server Qwen3-30B-A3B with expert-CPU offload (fit-test v2)
#   Status    : RAM/VRAM + loaded models
#   UnloadAll : reclaim everything (pre-heavy-op hygiene)
# Gates: every heavy load checks free RAM first (HostGuard discipline).

param([Parameter(Position=0)][string]$Profile = "Status")

$LMS = "$env:USERPROFILE\.lmstudio\bin\lms.exe"
$MODELS = "$env:USERPROFILE\.lmstudio\models"
$BACKEND = "$env:USERPROFILE\.lmstudio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.65.1"
$VENDOR = "$env:USERPROFILE\.lmstudio\extensions\backends\vendor\win-llama-cuda12-vendor-v2"
$LOG = "$env:USERPROFILE\Downloads\Apex-With-Triggers-Fixed\Logs"

function Get-FreeRAMGB {
    (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
}
function Get-FreeVRAMMB {
    try {
        $csv = & nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits
        [int]($csv[0].Trim())
    } catch { 0 }
}

function Wait-ModelLoaded([string]$key, [int]$timeoutSec = 180) {
    # JIT loading needs 15-40s on this box; wait until lms ps shows it GROWN
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        $ps = (& $LMS ps 2>$null | Out-String)
        if ($ps -match [regex]::Escape($key)) { Write-Host "  loaded: $key"; return $true }
        Start-Sleep -Seconds 5
    }
    Write-Host "  TIMEOUT waiting for $key"
    return $false
}

function Assert-CleanSlate {
    # unload anything that is not the target brain FIRST, then return measured free RAM
    # (unloading an idle 4-9GB model is strictly memory-safe and is what buys the space)
    $resident = (& $LMS ps 2>$null | Out-String)
    if ($resident -match "GENERATING") {
        Write-Host "a model is actively generating - refusing to swap mid-request"
        return $false
    }
    $needUnload = ($resident | Select-String "qwen2.5-coder|qwen2.5-14b|qwen3-30b|deepseek")
    if ($needUnload) {
        Write-Host "unloading resident wrong-brain models..."
        & $LMS unload --all
        Start-Sleep -Seconds 4
    }
    return $true
}

switch ($Profile) {
    "Status" {
        Write-Host ("RAM free : {0:N1} GB" -f (Get-FreeRAMGB))
        Write-Host ("VRAM free: {0} MB" -f (Get-FreeVRAMMB))
        & $LMS ps
    }
    "UnloadAll" {
        Write-Host "unloading all models..."
        & $LMS unload --all
        & $LMS ps
    }
    "Chat" {
        if (-not (Assert-CleanSlate)) { return }
        $free = Get-FreeRAMGB
        Write-Host ("RAM free after clean slate: {0:N1} GB (chat lane needs >= 5.0)" -f $free)
        if ($free -lt 5.0) { Write-Host "RAM GATE: close Chrome/Steam first."; return }
        Write-Host "loading chat brain (qwen3-8b) + draft speculative decoding..."
        & $LMS load qwen3-8b `
            --context-length 4096 `
            --parallel 2 `
            --speculative-draft-simple `
            --speculative-draft-model qwen3-0.6b `
            --speculative-draft-max-tokens 8
        Wait-ModelLoaded qwen3-8b | Out-Null
        Write-Host "chat lane: qwen3-8b (draft qwen3-0.6b) - identity = Qwen3-8B, NOT coder-7b"
    }
    "Code" {
        if (-not (Assert-CleanSlate)) { return }
        $free = Get-FreeRAMGB
        Write-Host ("RAM free after clean slate: {0:N1} GB (coding lane needs >= 6.5)" -f $free)
        if ($free -lt 6.5) { Write-Host "RAM GATE: free more memory first."; return }
        Write-Host "loading coding brain (14B) + draft speculative decoding..."
        & $LMS load qwen2.5-14b-instruct `
            --context-length 8192 `
            --parallel 1 `
            --ttl 7200 `
            --speculative-draft-simple `
            --speculative-draft-model qwen2.5-0.5b-instruct `
            --speculative-draft-max-tokens 6
        Wait-ModelLoaded qwen2.5-14b-instruct | Out-Null
        Write-Host "coding lane: 14B resident (draft 0.5B)"
    }
    "MoE" {
        # Fit-test v2: KTransformers-style. Attention/shared on GPU, experts on CPU.
        # Needs a quiet machine: >= 11.5 GB free RAM, LM Studio models unloaded.
        $free = Get-FreeRAMGB
        $vram = Get-FreeVRAMMB
        Write-Host ("RAM free: {0:N1} GB (needs >= 11.5) | VRAM free: {1} MB" -f $free, $vram)
        if ($free -lt 11.5) { Write-Host "RAM GATE: no other models may be loaded. Run UnloadAll + close Chrome/Steam."; return }
        $gguf = Get-ChildItem $MODELS -Recurse -Filter "*.gguf" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "qwen3-30b-a3b" } | Select-Object -First 1
        if (-not $gguf) { Write-Host "MoE gguf not found under $MODELS"; return }
        if (& $LMS ps 2>$null | Select-String "LOADED|GENERATING") {
            Write-Host "another model is loaded - refusing (fit-test must run alone)"; return
        }
        if (-not (Test-Path $VENDOR)) { Write-Host "cuda vendor dll dir missing: $VENDOR"; return }
        Write-Host "MoE fit-test v2: experts on CPU, attention on GPU (KTransformers recipe)"
        Write-Host "gguf: $($gguf.FullName)"
        $env:PATH = "$BACKEND;$VENDOR;$env:PATH"
        Start-Process -FilePath (Join-Path $BACKEND "llama-server.exe") `
            -ArgumentList @(
                "-m", $gguf.FullName,
                "-ngl", "999",
                "--n-cpu-moe", "999",
                "-fa", "on",
                "-ctk", "q8_0", "-ctv", "q8_0",
                "--ctx-size", "4096",
                "--parallel", "1",
                "--threads", "6",
                "--host", "127.0.0.1", "--port", "1235",
                "-md", (Get-ChildItem $MODELS -Recurse -Filter "*.gguf" | Where-Object { $_.Name -match "qwen3-0.6b" } | Select-Object -First 1 -ExpandProperty FullName),
                "--spec-draft-n-max", "8",
                "--spec-draft-device", "none"
            ) `
            -WorkingDirectory $BACKEND `
            -RedirectStandardOutput "$LOG\moe_server.out.log" `
            -RedirectStandardError  "$LOG\moe_server.err.log" `
            -NoNewWindow
        Write-Host "serving on http://127.0.0.1:1235 (logs in $LOG\moe_server.*.log)"
        Write-Host "watch RAM for 2 min; if free drops below 1.0 GB, kill llama-server (HostGuard)"
    }
    default { Write-Host "profiles: Chat | Code | MoE | Status | UnloadAll" }
}