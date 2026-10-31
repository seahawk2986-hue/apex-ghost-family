# Load-Checkpoint.ps1
[CmdletBinding()]
param()

$CheckpointPath = "$PSScriptRoot\..\Config\CheckpointState.json"
if (Test-Path $CheckpointPath) {
 return Get-Content $CheckpointPath | ConvertFrom-Json
}
return $null
