# Test-SkillIntegrity.ps1 - Lightweight validation gate (Pester-style)
[CmdletBinding()]
param(
 [string]$SkillPath
)

if (-not (Test-Path $SkillPath)) {
 return [PSCustomObject]@{ Passed = $false; Reason = "File missing" }
}

$Content = Get-Content $SkillPath -Raw

# Basic structural checks
$Checks = @(
 @{ Name = "Has CmdletBinding"; Pass = $Content -match "CmdletBinding" },
 @{ Name = "Has try/catch or error handling"; Pass = $Content -match "try|catch|ErrorAction" },
 @{ Name = "No banned integrity terms"; Pass = $Content -notmatch "spoof|fake_quota|hide_error|deceive|bypass_governor" },
 @{ Name = "Produces output or return"; Pass = $Content -match "return|Write-Host|Write-Output" },
 @{ Name = "Not empty"; Pass = $Content.Length -gt 50 }
)

$Failed = $Checks | Where-Object { -not $_.Pass }
$Passed = ($Failed.Count -eq 0)

return [PSCustomObject]@{
 Passed = $Passed
 Checks = $Checks
 Failed = $Failed.Name
}
