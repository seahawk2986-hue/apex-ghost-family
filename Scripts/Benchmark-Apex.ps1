# Benchmark-Apex.ps1 - Simple self-benchmark
[CmdletBinding()]
param()

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$ScriptsPath = Join-Path $Root "Scripts"

Write-Host "[Benchmark] Starting Apex self-benchmark..."

$sw = [System.Diagnostics.Stopwatch]::StartNew()

# Test 1: Skill generation
$Gen = & (Join-Path $ScriptsPath "New-Skill.ps1") -Request "benchmark skill" -SkillName "BenchmarkSkill"
$GenTime = $sw.ElapsedMilliseconds

# Test 2: Memory retrieval
$Mem = & (Join-Path $ScriptsPath "Get-SkillMemory.ps1") -Query "benchmark"
$MemTime = $sw.ElapsedMilliseconds - $GenTime

# Test 3: Reasoning
$Reason = & (Join-Path $ScriptsPath "Invoke-ReasoningLoop.ps1") -Goal "benchmark reasoning" -MaxSteps 2
$ReasonTime = $sw.ElapsedMilliseconds - $GenTime - $MemTime

$sw.Stop()

$Result = [PSCustomObject]@{
 Timestamp = (Get-Date).ToString("o")
 TotalMS = $sw.ElapsedMilliseconds
 GenerationMS = $GenTime
 MemoryMS = $MemTime
 ReasoningMS = $ReasonTime
 GenerationOK = $Gen
 MemoryCount = @($Mem).Count
 ReasoningSteps = @($Reason).Count
}

$BenchPath = Join-Path $Root "Config\BenchmarkResults.json"
if (Test-Path $BenchPath) {
 $Existing = Get-Content $BenchPath -Raw | ConvertFrom-Json
 $Existing += $Result
 $Existing | ConvertTo-Json -Depth 5 | Out-File $BenchPath -Encoding utf8
} else {
 @($Result) | ConvertTo-Json -Depth 5 | Out-File $BenchPath -Encoding utf8
}

Write-Host "[Benchmark] Total: $($Result.TotalMS)ms | Gen: $($Result.GenerationMS)ms | Mem: $($Result.MemoryMS)ms | Reason: $($Result.ReasoningMS)ms"
return $Result
