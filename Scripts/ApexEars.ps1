# ApexEars.ps1 - Apex HEARS. SAPI engine with GRAMMAR-based wake (robust) +
# dictation window for the command. Offline, built-in, $0. Commands POST to chat.
Add-Type -AssemblyName System.Speech

$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$Log = "$R\Logs\apex_ears.log"
$CfgPath = "$R\Config\ApexEars.json"
$pidMarker = "$R\Logs\apex_ears.pid"
$bootMarker = "$R\Logs\apex_ears_boot.log"

function Log($m) {
    $line = (Get-Date -Format s) + " " + $m
    try { Add-Content -Path $Log -Value $line -Encoding utf8 } catch {}
}

function Cfg {
    try { return (Get-Content $CfgPath -Raw -Encoding utf8 | ConvertFrom-Json) } catch { return $null }
}

function Speak($m) {
    $p = Cfg
    try { & $p.speak_script -Text $m -NoWatch | Out-Null } catch { Log "speak failed" }
}

function Toast($m) {
    $p = Cfg
    try { & $p.toast_script -Message $m | Out-Null } catch { Log "toast failed" }
}

function Send-ToApex($cmd) {
    $p = Cfg
    try {
        # THE AUTH-CURE: the serve = fail-closed (the 401 was honest); the
        # key = read from the file at send-time. Case-proof via $PSScriptRoot
        # (a bare $R here collides with the loop's $r recognition-result —
        # PowerShell vars are case-insensitive, that was the 20:28 crash).
        $kp = Join-Path (Split-Path -Parent $PSScriptRoot) "Config\apex_api.key"
        $key = (Get-Content $kp -Raw).Trim()
        $body = @{ message = $cmd } | ConvertTo-Json -Compress
        $rep = Invoke-RestMethod -Uri $p.chat_url -Method Post -Body $body `
            -ContentType "application/json" -Headers @{ "X-Apex-Key" = $key } `
            -TimeoutSec 90
        return $rep
    } catch {
        Log ("send failed: " + $_.Exception.Message)
        return $null
    }
}

if (-not (Test-Path $CfgPath)) {
    @{
        wake_word = "apex"
        chat_url = "http://127.0.0.1:8080/talk/api"
        speak_script = "$R\Scripts\ApexSpeak.ps1"
        toast_script = "$R\Scripts\ApexToast.ps1"
        speak_replies = $false
        muted = $false
        cmd_window_s = 9
        wake_min_conf = 0.5
    } | ConvertTo-Json | Set-Content -Path $CfgPath -Encoding utf8
}

[System.IO.File]::WriteAllText($pidMarker, [string]$PID)
try { [System.IO.File]::WriteAllText($bootMarker, ((Get-Date -Format s) + " boot pid=" + $PID)) } catch {}

# single-instance guard
$prevPath = "$pidMarker.bak"
if (Test-Path $prevPath) {
    try {
        $prevPid = [int](Get-Content $prevPath -First 1)
        $alive = Get-Process -Id $prevPid -ErrorAction SilentlyContinue
        if ($alive -and ($alive.ProcessName -match 'powershell')) {
            Log ("another ears (pid $prevPid) alive - exiting")
            exit 0
        }
    } catch {}
}
try { Copy-Item $pidMarker $prevPath -Force -ErrorAction SilentlyContinue } catch {}

Log "ears starting (SAPI grammar-wake + dictation-command)"

$p = Cfg
if ($p.muted) { Log "muted"; while ($true) { Start-Sleep -Seconds 10; $p = Cfg; if (-not $p.muted) { break } } }

$eng = $null
$wakeGrammar = $null
$dictGrammar = $null

function New-Engine {
    $e = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $e.SetInputToDefaultAudioDevice()
    $e.InitialSilenceTimeout = [TimeSpan]::FromSeconds(3)
    $e.BabbleTimeout = [TimeSpan]::FromSeconds(0)
    $e.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.5)
    return $e
}

try {
    $eng = New-Engine
    # wake grammar: exact-ish phrase matching (much stronger than dictation)
    $choices = New-Object System.Speech.Recognition.Choices
    $choices.Add("apex")
    $choices.Add("hey apex")
    $choices.Add("apx")
    $gb = New-Object System.Speech.Recognition.GrammarBuilder($choices)
    $wakeGrammar = New-Object System.Speech.Recognition.Grammar($gb)
    $wakeGrammar.Name = "wake"
    $eng.LoadGrammar($wakeGrammar)
    $dictGrammar = New-Object System.Speech.Recognition.DictationGrammar
    Log "engine ready: wake grammar loaded"
} catch {
    Log ("engine init failed: " + $_.Exception.Message)
    exit 1
}

$mode = "wake"            # wake | cmd
$cmdStart = $null
try {
    while ($true) {
        $p = Cfg
        if ($null -eq $p) { Start-Sleep -Seconds 5; continue }
        if ($p.muted) { Start-Sleep -Seconds 5; continue }

        $cap = [TimeSpan]::FromSeconds(3)
        if ($mode -eq "cmd") { $cap = [TimeSpan]::FromSeconds([double]$p.cmd_window_s) }
        try { $r = $eng.Recognize($cap) } catch {
            Log ("recognize error, reinit: " + $_.Exception.Message)
            try { $eng.Dispose() } catch {}
            $eng = New-Engine
            try {
                $eng.LoadGrammar($wakeGrammar)
                if ($mode -eq "cmd") { $eng.LoadGrammar($dictGrammar) }
            } catch {}
            Start-Sleep -Seconds 2
            continue
        }
        if (-not $r) {
            if ($mode -eq "cmd" -and $cmdStart -and
                ((Get-Date) - $cmdStart).TotalSeconds -gt [double]$p.cmd_window_s) {
                Log "command window closed without speech"
                try { $eng.UnloadGrammar($dictGrammar) } catch {}
                $eng.LoadGrammar($wakeGrammar)
                $mode = "wake"
            }
            continue
        }

        $heard = $r.Text.ToLower().Trim()
        $conf = [double]$r.Confidence
        $shown = $heard
        if ($shown.Length -gt 50) { $shown = $shown.Substring(0, 50) }
        Log ("heard [$mode]: '" + $shown + "' (conf " + [math]::Round($conf, 2) + ")")

        if ($mode -eq "wake") {
            if ($conf -lt [double]$p.wake_min_conf) { continue }
            if ($heard -match "apex|apx|a pex") {
                Log "wake word matched"
                # swap to dictation for the command
                try { $eng.UnloadGrammar($wakeGrammar) } catch {}
                $eng.LoadGrammar($dictGrammar)
                $mode = "cmd"
                $cmdStart = Get-Date
                Speak "Yes, Andrew?"
                continue
            }
            continue
        }

        # dictation mode: this is the command
        $cmd = $heard
        try { $eng.UnloadGrammar($dictGrammar) } catch {}
        $eng.LoadGrammar($wakeGrammar)
        $mode = "wake"
        if ($cmd -and $conf -ge 0.15) {
            Log ("command: '" + $cmd + "'")
            Toast ("Apex heard: " + $cmd)
            $rep = Send-ToApex $cmd
            if ($rep -and $rep.reply) {
                Speak ([string]$rep.reply)          # THE REAL ANSWER, SPOKEN
            } else {
                Speak ("On it. My answer is on the screen - the chat page or the toast.")
            }
        } else {
            Log "command rejected (empty/low conf)"
        }
    }
} catch {
    Log ("ears outer crash: " + $_.Exception.Message)
} finally {
    try { $eng.Dispose() } catch {}
    Log "ears stopped"
}
