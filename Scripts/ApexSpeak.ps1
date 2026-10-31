# ApexSpeak.ps1 - Apex SPEAKS a message aloud (Windows SAPI, built into the OS).
param([string]$Message = "Apex reporting in")
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = 1
$speak.SelectVoice(($speak.GetInstalledVoices() | Select-Object -First 1).Voice.Name)
$speak.Speak($Message)
$speak.Dispose()