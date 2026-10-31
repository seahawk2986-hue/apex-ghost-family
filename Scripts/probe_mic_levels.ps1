# probe_mic_levels.ps1 - audio level sampler (fix: PS syntax, no max())
Add-Type -AssemblyName System.Speech

Write-Host "SPEAK NOW - say 'test one two three' repeatedly"

$rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$rec.SetInputToDefaultAudioDevice()
$rec.InitialSilenceTimeout = [TimeSpan]::FromSeconds(0)

$level_total = 0
$level_max = 0
$level_count = 0
$heard_any = $false

for ($i = 0; $i -lt 20; $i++) {
    $level = $rec.AudioLevel
    $level_total += $level
    if ($level -gt $level_max) { $level_max = $level }
    $level_count++
    $r = $rec.Recognize([TimeSpan]::FromMilliseconds(250))
    if ($r) {
        $heard_any = $true
        Write-Host ("HEARD: '" + $r.Text + "' conf=" + [math]::Round([double]$r.Confidence,2))
    }
    Start-Sleep -Milliseconds 250
}

$avg = 0
if ($level_count -gt 0) { $avg = [math]::Round($level_total / $level_count, 1) }
Write-Host ""
Write-Host ("avg level: $avg | max: $level_max | heard: $heard_any | samples: $level_count")
if ($level_max -eq 0) {
    Write-Host "ZERO AUDIO: mic not feeding SAPI"
    Write-Host "Check: Windows Settings > Sound > Input - which device is DEFAULT?"
    Write-Host "Check: Is the mic muted or volume 0?"
    Write-Host "Check: Is Discord holding exclusive access?"
} elif (-not $heard_any) {
    Write-Host "AUDIO FLOWS but no recognition - try dictation grammar"
} else {
    Write-Host "AUDIO FLOWS and recognition works - the pipeline is LIVE"
}
$rec.Dispose()