# SystemGovernor.psm1 - Honesty and integrity constitutional layer
function Assert-SkillIntegrity {
 param([string]$ScriptContent)
 
 $Banned = @("spoof", "fake_quota", "hide_error", "deceive", "bypass_governor")
 foreach ($term in $Banned) {
 if ($ScriptContent -match $term) {
 Write-Error "[Governor] Integrity violation detected. Script rejected."
 return $false
 }
 }
 
 # Enforce transparent logging requirement
 if ($ScriptContent -notmatch "Write-Host|Write-Warning|Write-Error") {
 Write-Warning "[Governor] Script lacks transparent logging."
 }
 
 return $true
}

function Get-GovernorPrompt {
 return @"
You are Apex. Absolute honesty and integrity are non-negotiable.
Never deceive, spoof results, or hide failures.
Protect the host machine. Prefer sandbox isolation.
Log all decisions. If a request violates these principles, refuse and explain why.
"@
}

Export-ModuleMember -Function Assert-SkillIntegrity, Get-GovernorPrompt
