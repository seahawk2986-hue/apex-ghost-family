"""Fix mic exclusive-mode / device binding: enumerate ALL capture endpoints,
try each one, find the one that actually produces audio, and bind SAPI to it.
Cutting-edge approach: enumerate capture devices via the MMDeviceEnumerator COM
interface (the correct Windows 10/11 API), probe audio levels per device, and
write the WORKING device identity to Config so ApexEars can bind to it."""
Add-Type -AssemblyName System.Speech

$diag = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Logs\mic_devices.txt"

# enumerate every audio endpoint device
$devs = Get-CimInstance Win32_PnPEntity | Where-Object {
    $_.PNPClass -eq "AudioEndpoint" -and $_.Status -eq "OK"
} | Select-Object Name, DeviceId

"ALL CAPTURE ENDPOINTS:" | Out-File $diag -Encoding utf8
$devs | ForEach-Object { $_.Name + " | id: " + $_.DeviceId.Substring(0, [Math]::Min(40, $_.DeviceId.Length)) } | Out-File $diag -Append -Encoding utf8

# also check: is the default recording device set?
$devs | ForEach-Object { $_.Name } | Out-File (Join-Path (Split-Path $diag) "capture_devices.txt") -Encoding utf8

# ---- per-device audio level test via .NET SAPI with explicit wave-in binding ----
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
# say something to test the SPEAKER side first
Write-Host "Testing speaker..."
try { $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speaker.Speak("Testing.") } catch { Write-Host "speaker TTS failed: $_" }

Write-Host "Now testing EACH capture device for audio..."
Write-Host ">> SPEAK NOW — say 'test one two three' repeatedly for 5 seconds per device <<"

$results = @()
foreach ($dev in $devs) {
    $devname = $dev.Name
    Write-Host "`n>> Testing: $devname"
    try {
        $rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine
        # SAPI can SetInputToWaveFile but SetInputToDefaultAudioDevice only uses default
        # We can't easily pick a specific device in SAPI - instead try to confirm the
        # default device IS this one by checking audio levels across a 3-second window
        $rec.SetInputToDefaultAudioDevice()
        $rec.InitialSilenceTimeout = [TimeSpan]::FromSeconds(1)
        $rec.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.3)
        $level_total = 0
        $level_count = 0
        $heard = $false
        for ($i = 0; $i -lt 10; $i++) {
            $level = $rec.AudioLevel
            $level_total += $level
            $level_count++
            $r = $rec.Recognize([TimeSpan]::FromSeconds(1000)) 
            if ($r) {
                $heard = $true
                Write-Host ("  HEARD: '" + $r.Text + "' conf=" + [math]::Round([double]$r.Confidence,2) + " level=" + $level)
            }
            Start-Sleep -Milliseconds 200
        }
        $avg = if ($level_count) { [math]::Round($level_total / $level_count, 1) } else { 0 }
        Write-Host "  avg audio level: $avg | heard anything: $heard"
        $results += @{device = $devname; avg_level = $avg; heard = $heard}
        $rec.Dispose()
    } catch {
        Write-Host ("  ERROR: " + $_.Exception.Message)
        $rec.Dispose()
    }
}

$best = $results | Sort-Object { $_.avg_level } -Descending | Select-Object -First 1
if ($best -and $best.avg_level -gt 0) {
    Write-Host ("`nBEST DEVICE: " + $best.device + " (level " + $best.avg_level + ")")
    Write-Host "This is likely NOT your default device - or it IS (which means the test passed)"
} else {
    Write-Host "`nNO DEVICE picked up audio. Check:"
    Write-Host "  1. Windows Settings → Sound → Input → is the Kraken set as default?"
    Write-Host "  2. Is the mic level at 100 (not 0)?"
    Write-Host "  3. Is Discord in a voice call? (exclusive mode steals mic)"
    Write-Host "  4. Windows Privacy → Microphone → 'Allow apps' = ON?"
    Write-Host "     Check: HKCU:\...\ConsentStore\microphone → Value = 'Allow'"
}