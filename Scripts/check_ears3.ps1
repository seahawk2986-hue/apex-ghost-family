# check_ears3.ps1 - verify ApexEars3.ps1 parses
$p = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexEars3.ps1"
$e = $null; $t = $null
[System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$t, [ref]$e) | Out-Null
if ($e) {
    Write-Host ("AST ERRORS: " + $e.Count)
    $e | Select-Object -First 3 | ForEach-Object {
        Write-Host ("  line " + $_.Extent.StartLineNumber + ": " + $_.Message)
    }
} else {
    Write-Host "PARSE OK"
}