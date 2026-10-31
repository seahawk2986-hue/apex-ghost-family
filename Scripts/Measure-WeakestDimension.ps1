# Measure-WeakestDimension.ps1
# Simple measurement loop inspired by the harness standing goal
[CmdletBinding()]
param()

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$Scores = @{
 SkillGeneration = 6.5
 Validation = 7.0
 Memory = 7.5
 Reasoning = 7.0
 Research = 5.5
 Security = 6.5
 Persistence = 8.0
 SelfImprove = 7.5
}

$Weakest = $Scores.GetEnumerator() | Sort-Object Value | Select-Object -First 1

Write-Host "[Measure] Current dimension scores:"
$Scores.GetEnumerator() | Sort-Object Value | ForEach-Object {
 Write-Host (" {0,-18} {1}" -f $_.Key, $_.Value)
}

Write-Host "[Measure] Weakest dimension: $($Weakest.Key) ($($Weakest.Value))"
Write-Host "[Measure] Standing goal: improve weakest dimension without regressing others."

# Persist
$Out = Join-Path $Root "Config\DimensionScores.json"
$Scores | ConvertTo-Json | Out-File $Out -Encoding utf8

return $Weakest
