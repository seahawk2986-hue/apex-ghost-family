# Get-SkillMemory.ps1 - Retrieve and score past skills for reuse
[CmdletBinding()]
param(
 [string]$Query = ""
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$LogPath = Join-Path $Root "Config\SkillGenerationLog.json"
$HistoryPath = Join-Path $Root "Config\PerformanceHistory.json"

$Skills = @()

if (Test-Path $LogPath) {
 $Log = Get-Content $LogPath -Raw | ConvertFrom-Json
 $Skills += $Log | ForEach-Object {
 [PSCustomObject]@{
 Skill = $_.Skill
 Request = $_.Request
 Timestamp = $_.Timestamp
 Source = "GenerationLog"
 Score = 1.0
 }
 }
}

if (Test-Path $HistoryPath) {
 $Hist = Get-Content $HistoryPath -Raw | ConvertFrom-Json
 foreach ($h in $Hist) {
 if ($h.Winner) {
 $Skills += [PSCustomObject]@{
 Skill = $h.Skill
 Request = "MonteCarlo"
 Timestamp = $h.Timestamp
 Source = "PerformanceHistory"
 Score = [double]$h.Winner.ReliabilityScore / 100
 }
 }
 }
}

# Simple relevance boost if query matches
if ($Query) {
 $Skills = $Skills | ForEach-Object {
 if ($_.Request -match $Query -or $_.Skill -match $Query) {
 $_.Score += 0.5
 }
 $_
 }
}

$Ranked = $Skills | Sort-Object Score -Descending | Select-Object -First 5
Write-Host "[Memory] Retrieved $($Ranked.Count) relevant skills."
return $Ranked
