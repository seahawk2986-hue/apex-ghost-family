# Invoke-MonteCarloLoop.ps1 - Upgraded with basic real validation scoring
[CmdletBinding()]
param(
 [string]$TargetSkillName,
 [array]$CodeVariants,
 [int]$SimulationsPerVariant = 10
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$SkillsPath = Join-Path $Root "Skills"
$Results = @()

foreach ($Variant in $CodeVariants) {
 $Successes = 0
 $TotalTime = 0
 $Errors = @()
 
 for ($i = 1; $i -le $SimulationsPerVariant; $i++) {
 $sw = [System.Diagnostics.Stopwatch]::StartNew()
 try {
 # Execute variant in a constrained way
 $null = Invoke-Expression $Variant -ErrorAction Stop
 $Successes++
 }
 catch {
 $Errors += $_.Exception.Message
 }
 $sw.Stop()
 $TotalTime += $sw.ElapsedMilliseconds
 }
 
 $Reliability = [math]::Round(($Successes / $SimulationsPerVariant) * 100, 1)
 $AvgSpeed = [math]::Round($TotalTime / $SimulationsPerVariant, 1)
 
 $Results += [PSCustomObject]@{
 VariantSnippet = if ($Variant.Length -gt 60) { $Variant.Substring(0,60) + "..." } else { $Variant }
 ReliabilityScore = $Reliability
 AvgSpeedMS = $AvgSpeed
 ErrorCount = $Errors.Count
 RawScore = $Reliability - ($AvgSpeed / 10)
 }
}

$Winner = $Results | Sort-Object RawScore -Descending | Select-Object -First 1
Write-Host "[MonteCarlo] Best variant: $($Winner.ReliabilityScore)% reliability, $($Winner.AvgSpeedMS)ms avg"

# Persist result
$HistoryPath = Join-Path $Root "Config\PerformanceHistory.json"
$Entry = @{ Timestamp = (Get-Date).ToString("o"); Skill = $TargetSkillName; Winner = $Winner }
if (Test-Path $HistoryPath) {
 $Hist = Get-Content $HistoryPath -Raw | ConvertFrom-Json
 $Hist += $Entry
 $Hist | ConvertTo-Json -Depth 5 | Out-File $HistoryPath -Encoding utf8
} else {
 @($Entry) | ConvertTo-Json -Depth 5 | Out-File $HistoryPath -Encoding utf8
}

return $Winner
