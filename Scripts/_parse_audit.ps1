# THE PARSE-AUDIT: all parser errors in ApexEars.ps1, with line numbers.
$errs = $null
$toks = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexEars.ps1',
    [ref]$toks, [ref]$errs) | Out-Null
if (-not $errs -or $errs.Count -eq 0) {
    Write-Host 'PARSE: CLEAN'
} else {
    Write-Host ("PARSE ERRORS: " + $errs.Count)
    foreach ($e in $errs) {
        Write-Host ("L" + $e.Extent.StartLineNumber + " char" + $e.Extent.StartColumnNumber + ": " + $e.Message)
    }
}