# Invoke-SelfImprove.ps1 - Upgraded with research + multi-agent review
[CmdletBinding()]
param(
 [string]$Goal
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$ScriptsPath = Join-Path $Root "Scripts"

Write-Host "[SelfImprove] Starting advanced loop for: $Goal"

# 1. Memory
$Memory = & (Join-Path $ScriptsPath "Get-SkillMemory.ps1") -Query $Goal

# 2. Reasoning
$Reasoning = & (Join-Path $ScriptsPath "Invoke-ReasoningLoop.ps1") -Goal $Goal -MaxSteps 4

# 3. Research
$Insights = & (Join-Path $ScriptsPath "Get-ResearchInsights.ps1") -Topic $Goal -MaxResults 2

# 4. Decide
$ShouldGenerate = $true
if ($Memory -and ($Memory | Where-Object { $_.Score -gt 0.85 })) {
 Write-Host "[SelfImprove] Strong prior skill found. Reusing."
 $ShouldGenerate = $false
}

$GeneratedPath = $null
if ($ShouldGenerate) {
 $SkillName = "Improved-$(Get-Date -Format 'HHmmss')"
 $Success = & (Join-Path $ScriptsPath "New-Skill.ps1") -Request $Goal -SkillName $SkillName
 if ($Success) {
 $GeneratedPath = Join-Path $Root "Skills\$SkillName.ps1"
 Write-Host "[SelfImprove] Skill generated."
 
 # Multi-agent review
 $Review = & (Join-Path $ScriptsPath "Invoke-MultiAgentReview.ps1") -SkillPath $GeneratedPath
 if (-not $Review.Approved) {
 Write-Warning "[SelfImprove] Review failed. Skill remains in staging."
 }
 }
}

Write-Host "[SelfImprove] Advanced cycle complete."
return [PSCustomObject]@{
 Goal = $Goal
 Reused = -not $ShouldGenerate
 ReasoningSteps = $Reasoning.Count
 InsightsUsed = $Insights.Count
 Reviewed = $null -ne $GeneratedPath
}
