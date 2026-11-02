# THE PARSE-AUDIT v2: every PS file the voice-loop depends on.
$files = @(
    'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexEars.ps1',
    'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexSpeak.ps1'
)
foreach ($f in $files) {
    $errs = $null
    $toks = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $f, [ref]$toks, [ref]$errs) | Out-Null
    $name = Split-Path -Leaf $f
    if (-not $errs -or $errs.Count -eq 0) {
        $raw = [System.IO.File]::ReadAllBytes($f)
        $ascii = ($raw | Where-Object { $_ -gt 126 }).Count -eq 0
        Write-Host ($name + ": CLEAN" + $(if ($ascii) { " (pure-ASCII)" } else { " (NON-ASCII bytes!)" }))
    } else {
        Write-Host ($name + ": ERRORS " + $errs.Count)
        foreach ($e in $errs) {
            Write-Host ("  L" + $e.Extent.StartLineNumber + ": " + $e.Message)
        }
    }
}