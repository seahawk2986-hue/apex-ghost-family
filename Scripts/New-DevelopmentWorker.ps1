[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)]
 [string]$WorkerRole,
 [Parameter(Mandatory = $true)]
 [string]$TaskPayload
)

# New-DevelopmentWorker.ps1
$WorkerFolder = "$PSScriptRoot\..\SubAgents"
if (-not (Test-Path $WorkerFolder)) { New-Item -ItemType Directory -Path $WorkerFolder -Force | Out-Null }

$WorkerName = "Apex-Worker-$WorkerRole"
$WorkerPath = "$WorkerFolder\$WorkerName.ps1"

# Apex synthesizes a single-purpose, highly focused background script worker module
$WorkerScript = @"
# Automated Development Worker: $WorkerName
# Role: $WorkerRole
[CmdletBinding()]
param([string]`$Payload)

Write-Host "[$WorkerName] Task initialization sequence active..." -ForegroundColor Green
try {
 # Custom, focused logic built dynamically by Apex
 `$Result = Invoke-Expression -Command `$Payload
 return `$Result
} catch {
 Write-Error "[$WorkerName] Critical pipeline processing exception: `$($_.Exception.Message)"
}
"@

$WorkerScript | Out-File -FilePath $WorkerPath -Encoding utf8 -Force

# Launch the worker asynchronously via isolated low-priority jobs
Write-Host "[Apex Orchestrator] Spawning background worker: $WorkerName" -ForegroundColor Cyan
$Job = Start-Job -FilePath $WorkerPath -ArgumentList $TaskPayload -Name $WorkerName

return $Job
