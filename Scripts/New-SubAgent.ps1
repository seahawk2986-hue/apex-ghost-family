# New-SubAgent.ps1 - Sub-agent factory with Start-Job isolation
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$AgentName,
 [Parameter(Mandatory=$true)][string]$TaskType,
 [string]$TaskPayload = ""
)

$SubAgentCode = @"
[CmdletBinding()]
param([string]`$Payload)
try {
 Write-Host "[SubAgent:$AgentName] Starting task: $TaskType"
 # Isolated execution block
 `$Result = Invoke-Expression -Command `$Payload -ErrorAction Stop
 return [PSCustomObject]@{
 AgentName = '$AgentName'
 TaskType = '$TaskType'
 Success = `$true
 Result = `$Result
 Timestamp = (Get-Date).ToString('o')
 }
}
catch {
 return [PSCustomObject]@{
 AgentName = '$AgentName'
 TaskType = '$TaskType'
 Success = `$false
 Error = `$_.Exception.Message
 Timestamp = (Get-Date).ToString('o')
 }
}
"@

$Job = Start-Job -ScriptBlock ([scriptblock]::Create($SubAgentCode)) -ArgumentList $TaskPayload -Name $AgentName
return $Job
