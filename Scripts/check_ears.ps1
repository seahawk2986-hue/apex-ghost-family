# check_ears.ps1 - parse-check ApexEars.ps1 and report cleanly.
$p = 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexEars.ps1'
try {
    $null = [scriptblock]::Create((Get-Content -Raw $p))
    Write-Host 'PARSE OK'
} catch {
    Write-Host ('PARSE ERROR: ' + $_.Exception.Message)
    return
}
$tok = $null; $err = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tok, [ref]$err)
if ($err) {
    foreach ($e in $err) { Write-Host ('AST ERROR line ' + $e.Extent.StartLineNumber + ': ' + $e.Message) }
} else {
    Write-Host 'AST CLEAN (no syntax errors)'
}