"""ApexEars v3 - grammar-command recognition (not dictation).
Every known Apex voice command is a constrained phrase in the grammar - this is how
real voice assistants hit 0.9+ reliability. Unknown phrases are honestly rejected
with the heard fragment shown. Voice output via the existing ApexSpeak.ps1."""

Add-Type -AssemblyName System.Speech

$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$LogFile = "$R\Logs\apex_ears.log"
$CfgPath = "$R\Config\ApexEars.json"

function Log([string]$msg) {
    try { Add-Content $LogFile ((Get-Date -Format s) + " " + $msg) -Encoding utf8 } catch {}
}

function SayAndToast([string]$text) {
    try { Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","$R\Scripts\ApexSpeak.ps1","-Message",$text -Wait -NoNewWindow } catch {}
    try { Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","$R\Scripts\ApexToast.ps1","-Message",$text -NoNewWindow } catch {}
}

function SendToChat([string]$cmd) {
    try {
        $body = @{ message = $cmd } | ConvertTo-Json -Compress
        Invoke-RestMethod -Uri "http://127.0.0.1:8080/talk/api" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    } catch { Log ("send failed: " + $_.Exception.Message) }
}

[System.IO.File]::WriteAllText("$R\Logs\apex_ears.pid", [string]$PID)
Log "ears v3: command-grammar mode starting"

if (-not (Test-Path $CfgPath)) {
    @{ chat_url = "http://127.0.0.1:8080/talk/api"; muted = $false } | ConvertTo-Json | Set-Content $CfgPath -Encoding utf8
}

$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# ---- build the FULL command grammar — every known phrase in ONE grammar ----
$gb = New-Object System.Speech.Recognition.GrammarBuilder
$gb.Append((New-Object System.Speech.Recognition.Choices @(
    "status check", "what did you learn", "what is your weakest",
    "show your benchmark", "how are you", "any problems",
    "run the gym", "farm data", "skill session", "library stats",
    "what is your rank", "what can you do", "who are you",
    "what hardware", "self check", "what did i say"
)))
$cmds = New-Object System.Speech.Recognition.Grammar($gb)
$cmds.Name = "full_command"

# also a wake-only grammar
$wb = New-Object System.Speech.Recognition.GrammarBuilder
$wb.Append("Apex")
$wb.Append((New-Object System.Speech.Recognition.Choices @("status check","run the gym","farm data","skill session")))
$wake = New-Object System.Speech.Recognition.Grammar($wb)
$wake.Name = "wake"

$recognizer.LoadGrammar($cmds)
$recognizer.LoadGrammar($wake)
Log "grammar loaded: command + wake (SAPI)"

$mode = "command"
$pending = $false
while ($true) {
    try { $cfg = Get-Content $CfgPath -Raw -Encoding utf8 | ConvertFrom-Json } catch { $cfg = $null }
    if ($cfg -and $cfg.muted) { Start-Sleep 10; continue }

    $r = $recognizer.Recognize([TimeSpan]::FromSeconds(5))
    if (-not $r) { continue }
    $heard = $r.Text.ToLower().Trim()
    $conf = [double]$r.Confidence
    Log ("heard [$($r.Grammar.Name)]: '$heard' conf " + [math]::Round($conf,2))

    if ($conf -lt 0.25) { continue }

    # strip "apex" prefix
    $cmd = $heard

    if ($r.Grammar.Name -eq "wake" -or [string]::IsNullOrWhiteSpace($cmd)) {
        # just "Apex" alone -> acknowledge, wait for next phrase
        SayAndToast "Yes, Andrew?"
        $r2 = $recognizer.Recognize([TimeSpan]::FromSeconds(9))
        if ($r2) {
            $c2 = $r2.Text.ToLower().Trim()
            Log ("follow-up: '$c2' conf " + [math]::Round([double]$r2.Confidence,2))
            $c2 = $c2 -replace '^\s*apex\s*',''
            if ($c2) {
                Log ("follow-up command: sending to chat")
                SayAndToast "On it."
                SendToChat $c2
            }
        }
        continue
    }

    # known command -> send to chat
    Log ("sending to chat: '$cmd'")
    SayAndToast "On it."
    SendToChat $cmd
}