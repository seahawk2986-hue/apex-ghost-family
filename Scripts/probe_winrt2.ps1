# probe_winrt2.ps1 - find a workable constraint route for the WinRT recognizer.
Add-Type -AssemblyName System.Runtime.WindowsRuntime
try {
    $null = [Windows.Media.SpeechRecognition.SpeechRecognizer, Windows.Media.SpeechRecognition, ContentType = WindowsRuntime]
    Write-Host "stub recognizer: OK"
} catch {
    Write-Host "stub recognizer FAILED: " + $_.Exception.Message
    return
}

try {
    $null = [Windows.Media.SpeechRecognition.ISpeechRecognitionConstraint, Windows.Media.SpeechRecognition, ContentType = WindowsRuntime]
    Write-Host "stub ISpeechRecognitionConstraint: OK"
} catch {
    Write-Host "stub ISpeechRecognitionConstraint FAILED: " + $_.Exception.Message
}

$rec = New-Object Windows.Media.SpeechRecognition.SpeechRecognizer("en-US")
Write-Host ("recognizer created: " + ($rec -ne $null))

$made = $null
try { $made = New-Object Windows.Media.SpeechRecognition.DictationConstraint } catch { Write-Host ("New-Object DictationConstraint FAILED: " + $_.Exception.Message) }
if ($made) { Write-Host "DictationConstraint created" }
if (-not $made) {
    try {
        $words = New-Object "System.Collections.Generic.IList[string]"
        $words.Add("apex"); $words.Add("hey apex")
        $made = New-Object Windows.Media.SpeechRecognition.SpeechRecognitionListConstraint($words)
        Write-Host "SpeechRecognitionListConstraint created"
    } catch {
        Write-Host ("List constraint FAILED: " + $_.Exception.Message)
    }
}
if (-not $made) { Write-Host "NO constraint type can be built - WinRT route blocked"; return }

try {
    $rec.Constraints.Add($made) | Out-Null
    Write-Host "Constraints.Add: OK"
} catch {
    Write-Host ("Constraints.Add FAILED: " + $_.Exception.Message)
    return
}

try {
    $op = $rec.CompileConstraintsAsync()
    Start-Sleep -Seconds 3
    $compiled = $op.GetResults()
    Write-Host ("compile status: " + $compiled.Status)
    if ([string]$compiled.Status -eq 'Success') { Write-Host "WINRT ROUTE WORKABLE" }
} catch {
    Write-Host ("compile failed: " + $_.Exception.Message)
}