[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)]
 [string]$ServerUrl,
 [Parameter(Mandatory = $true)]
 [string]$ToolName,
 [Parameter(Mandatory = $true)]
 [hashtable]$Arguments
)

# Invoke-StatelessMcp.ps1
Write-Host "[MCP 2026] Executing stateless context transmission frame..." -ForegroundColor Cyan

# Pack protocol configuration dynamically inside the _meta fields
$RequestPacket = @{
 jsonrpc = "2.0"
 id = [Guid]::NewGuid().ToString()
 method = "tools/call"
 params = @{
 name = $ToolName
 arguments = $Arguments
 _meta = @{
 "io.modelcontextprotocol/protocol" = "2026.1"
 "io.modelcontextprotocol/client" = @{
 sampling = @{}
 roots = @{ listChanged = $false }
 }
 }
 }
} | ConvertTo-Json -Depth 10

try {
 $Headers = @{ "Content-Type" = "application/json" }
 # Stateless delivery means 0ms handshake overhead over web pipes
 $Response = Invoke-RestMethod -Uri $ServerUrl -Method Post -Body $RequestPacket -Headers $Headers -TimeoutSec 15
 return $Response.result.content
} catch {
 Write-Warning "[MCP 2026 Failure] Stateless delivery node connection drop."
 return $null
}
