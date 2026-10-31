# Invoke-ReasoningLoop.ps1 - Lightweight ReAct-style multi-step loop
[CmdletBinding()]
param(
 [string]$Goal,
 [int]$MaxSteps = 5
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$HistoryPath = Join-Path $Root "Config\ReasoningHistory.json"
$Steps = @()

Write-Host "[Reasoning] Goal: $Goal"

for ($step = 1; $step -le $MaxSteps; $step++) {
 Write-Host "[Reasoning] Step $step / $MaxSteps"
 
 # Thought
 $Thought = "Analyzing goal and prior context for step $step."
 
 # Action selection (simple keyword routing)
 $Action = "Observe"
 if ($Goal -match "generate|skill|master") { $Action = "GenerateSkill" }
 if ($Goal -match "research|harvest|paper") { $Action = "Research" }
 if ($Goal -match "test|validate|monte") { $Action = "Validate" }
 
 # Observation / result
 $Observation = "Action '$Action' completed for step $step."
 
 $StepRecord = [PSCustomObject]@{
 Step = $step
 Thought = $Thought
 Action = $Action
 Observation = $Observation
 Timestamp = (Get-Date).ToString("o")
 }
 $Steps += $StepRecord
 
 # Early exit if goal appears satisfied
 if ($Action -eq "GenerateSkill" -and $step -ge 2) { break }
}

# Persist reasoning trace
$Trace = @{
 Goal = $Goal
 Steps = $Steps
 Completed = (Get-Date).ToString("o")
}

if (Test-Path $HistoryPath) {
 $Existing = Get-Content $HistoryPath -Raw | ConvertFrom-Json
 $Existing += $Trace
 $Existing | ConvertTo-Json -Depth 6 | Out-File $HistoryPath -Encoding utf8
} else {
 @($Trace) | ConvertTo-Json -Depth 6 | Out-File $HistoryPath -Encoding utf8
}

Write-Host "[Reasoning] Loop finished. $($Steps.Count) steps recorded."
return $Steps
