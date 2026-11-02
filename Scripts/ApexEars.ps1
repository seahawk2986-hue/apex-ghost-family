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
        # (a bare $R here collides with the loop's $r recognition-result -
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

# == THE PAPER-BACKED VOICE SET (all pure code = zero RAM, zero VRAM) ==
$script:Acks = @("Yes, Andrew?", "Go ahead.", "I'm listening.", "Mm-hm?")
$script:AckIdx = 0
$script:echoUntil = Get-Date -Date "2000-01-01"
$script:retried = $false
$script:pendingDanger = $null

function Speak-Clean($m) {
    # THE FLATTENER: markdown-to-prose so the TTS never says "star star"
    # or "hash" (the spoken-reply etiquette; the brain also emits prose
    # by instruction - this is the belt for whatever slips through)
    $t = [string]$m
    $t = $t -replace '(?m)^#{1,6}\s*', ''
    $t = $t -replace '\*\*([^*]+)\*\*', '$1'
    $t = $t -replace '\*([^*]+)\*', '$1'
    $t = $t -replace '```[\s\S]*?```', '(code shown on screen)'
    $t = $t -replace '`([^`]+)`', '$1'
    $t = $t -replace '\[([^\]]+)\]\(http[^)]+\)', '$1'
    $t = $t -replace 'https?://\S+', '(a link, on screen)'
    $t = $t -replace '\n{2,}', '. '
    $t = $t -replace '\s+', ' '
    return $t.Trim()
}

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

        # THE ECHO-GUARD: right after Apex speaks, his own TTS lands in
        # the mic (the self-echo fiction that consumes voice agents); a
        # low-confidence row inside 5-7s after speech = my own voice's
        # tail, suppressed. Real wakes (0.7-0.95) always pass.
        if ((Get-Date) -lt $script:echoUntil -and $conf -lt 0.55) {
            Log "echo-guard: own-voice tail suppressed"
            continue
        }

        if ($mode -eq "wake") {
            if ($conf -lt [double]$p.wake_min_conf) { continue }
            if ($heard -match "apex|apx|a pex") {
                Log "wake word matched"
                # swap to dictation for the command
                $script:retried = $false
                try { $eng.UnloadGrammar($wakeGrammar) } catch {}
                $eng.LoadGrammar($dictGrammar)
                $mode = "cmd"
                $cmdStart = Get-Date
                Speak $script:Acks[$script:AckIdx % $script:Acks.Count]
                $script:AckIdx++
                $script:echoUntil = (Get-Date).AddSeconds(5)
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
            # THE CONFIRM-GATE (destructive-verb protection, spoken confirm;
            # any later confirm-phrase releases the stashed command)
            if ($script:pendingDanger -and
                    $cmd -match "(do it|confirm|yes|sure|go ahead)") {
                $cmd = $script:pendingDanger
                $script:pendingDanger = $null
                Log ("confirmed: '" + $cmd + "'")
            } elseif ($cmd -match "(delete|wipe|erase|format|uninstall|kill)" -and
                      -not $script:pendingDanger) {
                $script:pendingDanger = $cmd
                Log "danger-verb: spoken confirm pending"
                Speak "That sounds irreversible. Say: Apex do it, to confirm."
                $script:echoUntil = (Get-Date).AddSeconds(7)
                continue
            } else {
                $script:pendingDanger = $null
            }
            Log ("command: '" + $cmd + "'")
            # THE ONE-SEC BACKCHANNEL (the data-driven delay-disclosure:
            # if the brain's last ttft was slow, acknowledge the wait)
            $slow = $false
            try {
                $mm = Get-Content (Join-Path (Split-Path -Parent $PSScriptRoot) "Config\ChatMetrics.json") -Raw |
                    ConvertFrom-Json
                $last = $mm.recent[-1].ttft_s
                if ($last -and [double]$last -gt 8) { $slow = $true }
            } catch {}
            if ($slow) {
                Speak "One second."
                $script:echoUntil = (Get-Date).AddSeconds(5)
            }
            Toast ("Apex heard: " + $cmd)
            $rep = Send-ToApex $cmd
            if ($rep -and $rep.reply) {
                $clean = Speak-Clean $rep.reply
                if (-not $clean) { $clean = [string]$rep.reply }
                if ($clean.Length -gt 400) {
                    # THE PACE-CURE (long reply = a notch faster, the
                    # listening-comfort standard; -Rate = SAPI -10..10)
                    & $p.speak_script -Text $clean -Rate 1 -NoWatch | Out-Null
                } else {
                    Speak $clean
                }
            } else {
                Speak ("On it. My answer is on the screen - the chat page or the toast.")
            }
            $script:echoUntil = (Get-Date).AddSeconds(7)
        } else {
            Log "command rejected (empty/low conf)"
            # THE REPAIR-RETRY (the clarify-request: one second chance,
            # never a loop; natural wakes reset it)
            if (-not $script:retried) {
                $script:retried = $true
                Speak "Say that again?"
                $script:echoUntil = (Get-Date).AddSeconds(5)
                try { $eng.UnloadGrammar($wakeGrammar) } catch {}
                $eng.LoadGrammar($dictGrammar)
                $mode = "cmd"
                $cmdStart = Get-Date
            }
        }
    }
} catch {
    Log ("ears outer crash: " + $_.Exception.Message)
} finally {
    try { $eng.Dispose() } catch {}
    Log "ears stopped"
}
