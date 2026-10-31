# Save-Checkpoint.ps1 - Durable event-driven checkpoint
[CmdletBinding()]
param(
 [object]$StateObject
)

$CheckpointPath = "$PSScriptRoot\..\Config\CheckpointState.json"

$Checkpoint = [PSCustomObject]@{
 LastCheckpoint = (Get-Date).ToString("o")
 ActiveVariables = $StateObject.Variables
 CompiledFragments = $StateObject.Fragments
 SubAgentManifests = $StateObject.Manifests
 CurriculumPosition = $StateObject.Position
}

$Checkpoint | ConvertTo-Json -Depth 6 | Out-File $CheckpointPath -Encoding utf8
Write-Host "[Checkpoint] State saved."
