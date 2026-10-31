# Invoke-AgentRecruitment.ps1 - Swarm recruitment via MCP
[CmdletBinding()]
param(
 [string]$TaskDescription,
 [string[]]$TargetEndpoints
)

$Results = @()

foreach ($Endpoint in $TargetEndpoints) {
 $ContractPayload = @{
 jsonrpc = "2.0"
 id = [Guid]::NewGuid().ToString()
 method = "tools/call"
 params = @{
 name = "execute_task"
 arguments = @{ task = $TaskDescription }
 }
 } | ConvertTo-Json -Depth 5
 
 try {
 $Response = Invoke-RestMethod -Uri $Endpoint -Method Post -Body $ContractPayload -ContentType "application/json" -TimeoutSec 15
 $Results += [PSCustomObject]@{
 Endpoint = $Endpoint
 Success = $true
 Output = $Response.result
 }
 }
 catch {
 $Results += [PSCustomObject]@{
 Endpoint = $Endpoint
 Success = $false
 Error = $_.Exception.Message
 }
 }
}

return $Results
