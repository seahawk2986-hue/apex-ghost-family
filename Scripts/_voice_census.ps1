# THE VOICE-CENSUS: every SAPI voice installed on this box, no install, $0.
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
Write-Host "[installed SAPI voices]:"
foreach ($v in $s.GetInstalledVoices()) {
    $vi = $v.VoiceInfo
    Write-Host ("  id=" + $vi.Id)
    Write-Host ("    name=" + $vi.Name + "  gender=" + $vi.Gender +
                "  culture=" + $vi.Culture.Name +
                "  age=" + $vi.Age)
}
Write-Host ("[default]: " + $s.Voice.Name)