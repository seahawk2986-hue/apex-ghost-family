# ApexEarsCheck.ps1 - verify built-in offline speech recognition availability.
Add-Type -AssemblyName System.Speech
Write-Host ("recognition type present: " +
    [bool][System.Speech.Recognition.SpeechRecognitionEngine])
$rs = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
Write-Host ("recognizer count: " + $rs.Count)
foreach ($r in $rs) {
    Write-Host ("recognizer: " + $r.Culture.Name + " | " + $r.Id + " | " + $r.Description)
}
# 3-second off-air sanity test: init engine, load dictation, no transcript asserted.
try {
    $eng = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $eng.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
    $eng.SetInputToDefaultAudioDevice()
    Write-Host "engine init + dictation grammar + default mic input: OK"
    $eng.Dispose()
} catch {
    Write-Host ("engine init test failed: " + $_.Exception.Message)
}