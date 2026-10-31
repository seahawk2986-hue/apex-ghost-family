"""Deep diagnostic: capture what the recognizer ACTUALLY processes right now.

Log EVERYTHING to a file: audio device binding, confidence values even for low-conf
results, every partial result, the exact grammar name that matched, the engine state.
Runs for 30 seconds then writes a full diagnostic dump."""
Add-Type -AssemblyName System.Speech

$diag_path = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Logs\ears_diag.txt"
$e = $null; $t = $null

function DiagLog($msg) {
    Add-Content $diag_path ((Get-Date -Format "HH:mm:ss.fff") + " $msg") -Encoding utf8
}

try {
    [System.IO.File]::WriteAllText($diag_path, ("DIAG START " + (Get-Date -Format s) + "`n"))

    $rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    DiagLog ("recognizer created: " + ($rec -ne $null))

    $rec.SetInputToDefaultAudioDevice()
    DiagLog "input: default audio device"

    $rec.InitialSilenceTimeout = [TimeSpan]::FromSeconds(2)
    $rec.BabbleTimeout = [TimeSpan]::FromSeconds(0)
    $rec.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.5)

    # grammar 1: wake word
    $gb1 = New-Object System.Speech.Recognition.GrammarBuilder
    $gb1.Append("Apex")
    $g1 = New-Object System.Speech.Recognition.Grammar($gb1)
    $g1.Name = "wake"
    $rec.LoadGrammar($g1)
    DiagLog ("grammar 'wake' loaded: " + $g1.Name)

    # grammar 2: command phrases
    $gb2 = New-Object System.Speech.Recognition.GrammarBuilder
    $gb2.Append("status check")
    $g2 = New-Object System.Speech.Recognition.Grammar($gb2)
    $g2.Name = "cmd_status"
    $rec.LoadGrammar($g2)
    DiagLog ("grammar 'cmd_status' loaded")

    # grammar 3: what did you learn
    $gb3 = New-Object System.Speech.Recognition.GrammarBuilder
    $gb3.Append("what did you learn")
    $g3 = New-Object System.Speech.Recognition.Grammar($gb3)
    $g3.Name = "cmd_learn"
    $rec.LoadGrammar($g3)
    DiagLog ("grammar 'cmd_learn' loaded")

    # audio level monitoring
    DiagLog ("audio format: " + $rec.AudioFormat)
    DiagLog ("recognizer state: " + $rec.State)
    DiagLog ("enabled: " + $rec.Enabled)

    DiagLog "--- LISTENING PHASE (20 seconds) - SPEAK NOW ---"

    $cycle = 0
    $endTime = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $endTime) {
        try {
            $level = $rec.AudioLevel
            $result = $rec.Recognize([TimeSpan]::FromSeconds(2))
            $cycle++
            if ($result) {
                $conf = [math]::Round([double]$result.Confidence, 3)
                $text = $result.Text
                $gram = if ($result.Grammar) { $result.Grammar.Name } else { "none" }
                DiagLog ("HEARD: '$text' conf=$conf grammar=$gram")
                $alts = $result.Alternates
                foreach ($alt in $alts) {
                    DiagLog ("  alt: '" + $alt.Text + "' conf=" + [math]::Round([double]$alt.Confidence,3))
                }
            } else {
                DiagLog ("cycle $cycle`: null result | audioLevel=$level")
            }
        } catch {
            DiagLog ("ERROR: " + $_.Exception.Message)
        }
    }
    DiagLog "listening phase complete"

    # audio level was being tracked
    DiagLog ("final audio level: " + $rec.AudioLevel)

    # try direct dictation for comparison
    DiagLog "--- DICTATION COMPARISON (5 seconds) ---"
    $dg = New-Object System.Speech.Recognition.DictationGrammar
    $rec.UnloadAllGrammars()
    $rec.LoadGrammar($dg)
    $r2 = $rec.Recognize([TimeSpan]::FromSeconds(5))
    if ($r2) {
        DiagLog ("dictation heard: '" + $r2.Text + "' conf=" + [math]::Round([double]$r2.Confidence,3))
    } else {
        DiagLog "dictation: null (no speech detected in 5s)"
    }

    # restore command grammar
    $rec.UnloadGrammar($dg)
    $rec.LoadGrammar($g1)
    $rec.LoadGrammar($g2)
    $rec.LoadGrammar($g3)

    DiagLog "DIAG COMPLETE"
} catch {
    DiagLog ("FATAL: " + $_.Exception.ToString())
}

Write-Host "done - read $diag_path"