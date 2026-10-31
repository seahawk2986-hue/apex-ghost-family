# Policy-Integrity.ps1
# Stronger integrity rules inspired by the latest apex_harness.py
[CmdletBinding()]
param(
 [string]$ProposedAction,
 [string]$Content = ""
)

$BlockedPatterns = @(
 "rm -rf /",
 "rm -rf ~",
 "format-disk",
 "shutdown",
 "reboot",
 "sudo ",
 "fork bomb"
)

foreach ($Pattern in $BlockedPatterns) {
 if ($ProposedAction -match [regex]::Escape($Pattern) -or $Content -match [regex]::Escape($Pattern)) {
 Write-Warning "[Integrity] Blocked dangerous action: $Pattern"
 return $false
 }
}

# Never invent results
if ($Content -match "I (ran|tested|verified)" -and $Content -notmatch "pytest|Invoke-Pester|actual output") {
 Write-Warning "[Integrity] Claim of testing without evidence."
 return $false
}

Write-Host "[Integrity] Action cleared."
return $true
