# ApexSpeak.ps1 - Apex SPEAKS a message aloud (Windows SAPI, built into the OS).
param([string]$Message = "Apex reporting in")
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = 1
# Only select a voice whose name is non-empty; SAPI's default is fine otherwise.
$voices = @($speak.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name })
foreach ($want in @('Microsoft David', 'Microsoft Zira', 'Microsoft Mark', 'Microsoft Hazel', 'Microsoft George')) {
    $hit = $voices | Where-Object { $_.VoiceInfo.Name -like "*$want*" } | Select-Object -First 1
    if ($hit) { $speak.SelectVoice($hit.VoiceInfo.Name); break }
}
$speak.Speak($Message)
$speak.Dispose()