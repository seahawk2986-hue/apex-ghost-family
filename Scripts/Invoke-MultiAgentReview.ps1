# Invoke-MultiAgentReview.ps1 - Lightweight multi-perspective review
[CmdletBinding()]
param(
 [string]$SkillPath
)

if (-not (Test-Path $SkillPath)) {
 return @{ Approved = $false; Reason = "Missing file" }
}

$Content = Get-Content $SkillPath -Raw
$Reviews = @()

# Reviewer 1: Integrity
$Integrity = $Content -notmatch "spoof|fake|deceive|bypass"
$Reviews += @{ Reviewer = "Integrity"; Pass = $Integrity; Note = "No banned terms" }

# Reviewer 2: Structure
$Structure = $Content -match "CmdletBinding" -and $Content -match "try"
$Reviews += @{ Reviewer = "Structure"; Pass = $Structure; Note = "Has binding and error handling" }

# Reviewer 3: Observability
$Observability = $Content -match "Write-Host|Write-Error|return"
$Reviews += @{ Reviewer = "Observability"; Pass = $Observability; Note = "Produces output" }

$Approved = ($Reviews | Where-Object { -not $_.Pass }).Count -eq 0

Write-Host "[Review] Approved: $Approved"
return [PSCustomObject]@{
 Approved = $Approved
 Reviews = $Reviews
}
