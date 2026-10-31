# Start-TokenDaemon.ps1
# Background loop that refreshes MCP/OAuth tokens from configured endpoints
# (implements the token automation described in the Gemini thread)
[CmdletBinding()]
param(
 [int]$RefreshIntervalSeconds = 3600,
 [string]$ConfigPath = "$PSScriptRoot\..\Config\ResourceRegistry.json"
)

Write-Host "[TokenDaemon] Starting. Refresh interval: $RefreshIntervalSeconds seconds"

while ($true) {
 try {
 if (-not (Test-Path $ConfigPath)) {
 Write-Warning "[TokenDaemon] Registry not found. Sleeping."
 Start-Sleep -Seconds $RefreshIntervalSeconds
 continue
 }

 $Registry = Get-Content $ConfigPath -Raw | ConvertFrom-Json

 # Look for pools that have an OAuth-style endpoint
 $TokenPools = $Registry.Pools | Where-Object {
 $_.ProviderName -match "MCP|OAuth|Token" -or
 ($_.EndpointUrl -and $_.EndpointUrl -match "oauth|token|mcp")
 }

 foreach ($Pool in $TokenPools) {
 if (-not $Pool.EndpointUrl) { continue }

 Write-Host "[TokenDaemon] Refreshing token for $($Pool.ProviderName)..."

 # Call the existing Automate-McpTokens logic
 $Success = & "$PSScriptRoot\Automate-McpTokens.ps1" -TargetMcpServerUrl $Pool.EndpointUrl -ConfigPath $ConfigPath

 if ($Success) {
 Write-Host "[TokenDaemon] Token refreshed for $($Pool.ProviderName)."
 }
 else {
 Write-Warning "[TokenDaemon] Refresh failed for $($Pool.ProviderName)."
 }
 }

 # Memory cleanup
 [System.GC]::Collect()
 }
 catch {
 Write-Warning "[TokenDaemon] Loop error: $_"
 }

 Start-Sleep -Seconds $RefreshIntervalSeconds
}
