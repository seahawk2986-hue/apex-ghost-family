# check_ears3_v2.ps1 - just check parse
$p = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexEars3.ps1"
$e = $null; $t = $null
[System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$t, [ref]$e) | Out-Null
if ($e) { Write-Host ("PARSE ERRORS: " + $e.Count); $e | Select-Object -First 2 | ForEach-Object { Write-Host ("  " + $_.Message) } }
else { Write-Host "PARSE OK" }
# check the grammar has no Apex prefix in the command builder
$c = Get-Content $p -Raw -Encoding utf8
if ($c.Contains('$gb.Append("Apex")')) { Write-Host "WARN: Apex prefix still in command grammar" }
else { Write-Host "command grammar: no wake prefix (direct commands only)" }