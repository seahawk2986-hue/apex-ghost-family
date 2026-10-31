# Start-WeeklyPurge.ps1
# Weekly self-purge routine described in the Gemini thread
[CmdletBinding()]
param(
 [string]$ConfigFolder = "$PSScriptRoot\..\Config",
 [int]$KeepCheckpoints = 3
)

Write-Host "[WeeklyPurge] Starting cleanup..."

# Keep only the N most recent checkpoints
$Checkpoints = Get-ChildItem -Path $ConfigFolder -Filter "CheckpointState*.json" -ErrorAction SilentlyContinue
if ($Checkpoints -and $Checkpoints.Count -gt $KeepCheckpoints) {
 $Checkpoints | Sort-Object LastWriteTime -Descending | Select-Object -Skip $KeepCheckpoints | Remove-Item -Force
 Write-Host "[WeeklyPurge] Old checkpoints removed."
}

# Compress old logs if any
$Logs = Get-ChildItem -Path $ConfigFolder -Filter "*.log" -ErrorAction SilentlyContinue
foreach ($Log in $Logs) {
 if ($Log.Length -gt 1MB) {
 Write-Host "[WeeklyPurge] Large log detected: $($Log.Name)"
 # In full version: Compress-Archive or gzip
 }
}

Write-Host "[WeeklyPurge] Complete."
return $true
