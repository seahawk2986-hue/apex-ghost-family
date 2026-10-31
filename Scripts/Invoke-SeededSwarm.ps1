# Invoke-SeededSwarm.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)][string]$RequiredSpecialty,
 [Parameter(Mandatory = $true)][hashtable]$TaskArguments
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$RegistryPath = Join-Path $Root "Config\SeededNodes.json"

if (-not (Test-Path $RegistryPath)) { 
 Write-Warning "[Swarm] Seeded nodes registry not found."
 return $null 
}

# 1. Read your private web worker registry
$Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json
$TargetNode = $Registry.SeededNodes | Where-Object { $_.Specialty -eq $RequiredSpecialty -and $_.Status -eq "Dormant-Ready" } | Select-Object -First 1

if (-not $TargetNode) {
 Write-Warning "[Swarm] No dormant workers found with specialty: $RequiredSpecialty. Falling back to public free pools."
 return $null
}

Write-Host "[Swarm] Waking up pre-seeded worker node: $($TargetNode.NodeID) ($($TargetNode.EndpointUrl))..." -ForegroundColor Yellow

# 2. Package the stateless 2026 JSON-RPC request format
$Payload = @{
 jsonrpc = "2.0"
 id = [Guid]::NewGuid().ToString()
 method = "tools/call"
 params = @{
 name = "execute_swarm_subtask"
 arguments = $TaskArguments
 _meta = @{
 "io.modelcontextprotocol/protocolVersion" = "2026-07-28"
 }
 }
} | ConvertTo-Json -Depth 10

try {
 $Headers = @{ "Content-Type" = "application/json" }
 
 # 3. Hit the endpoint
 $Response = Invoke-RestMethod -Uri $TargetNode.EndpointUrl -Method Post -Body $Payload -Headers $Headers -TimeoutSec 20
 Write-Host "[Swarm] Worker completed task and returned to dormant standby sleep." -ForegroundColor Green
 
 return $Response.result.content
}
catch {
 Write-Warning "[Swarm] Seeded node failed to wake up or timed out: $($_.Exception.Message)"
 return $null
}
