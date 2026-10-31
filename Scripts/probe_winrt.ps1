# probe_winrt.ps1 - find the working WinRT projection form, then verify SR setup.
Add-Type -AssemblyName System.Runtime.WindowsRuntime

try {
    $null = [Windows.Media.SpeechRecognition.SpeechRecognizer, Windows.Media.SpeechRecognition, ContentType = WindowsRuntime]
    Write-Host "step1 stub SpeechRecognizer: OK"
} catch {
    Write-Host ("step1 FAILED: " + $_.Exception.Message)
    return
}

# after module load, plain syntax should resolve
try {
    $null = [Windows.Media.SpeechRecognition.DictationConstraint]
    Write-Host "step2 plain DictationConstraint: OK"
} catch {
    Write-Host ("step2 FAILED: " + $_.Exception.Message)
}

try {
    $rec = New-Object Windows.Media.SpeechRecognition.SpeechRecognizer("en-US")
    Write-Host "step3 recognizer created"
    $dg = New-Object Windows.Media.SpeechRecognition.DictationConstraint
    try {
        $rec.Constraints.Add($dg) | Out-Null
        Write-Host "step4 .Add constraint: OK"
    } catch {
        Write-Host ("step4 FAILED: " + $_.Exception.Message)
    }
    $res = $rec.CompileConstraintsAsync()
    $t = $res.GetType().GetMethod("GetResults")
    Start-Sleep -Seconds 2
    try {
        $compiled = $res.GetResults()
        Write-Host ("step5 compile status: " + $compiled.Status)
    } catch {
        Write-Host ("step5 getresults failed: " + $_.Exception.Message)
    }
    Write-Host ("recognizer state: " + $rec.State)
} catch {
    Write-Host ("step3+ FAILED: " + $_.Exception.Message)
}