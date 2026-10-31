# New-TokenScout.ps1
# Sub-agent factory specifically for token refresh tasks
# (creates an isolated job that runs the token daemon logic)
[CmdletBinding()]
param(
 [string]$TargetEndpoint,
 [int]$IntervalSeconds = 3600
)

$ScoutCode = @"
[CmdletBinding()]
param([string]`$Endpoint, [int]`$Interval)
`$ConfigPath = '`$PSScriptRoot\..\Config\ResourceRegistry.json'
while (`$true) {
 try {
 Write-Host "[TokenScout] Refreshing `$Endpoint"
 & '`$PSScriptRoot\Automate-McpTokens.ps1' -TargetMcpServerUrl `$Endpoint -ConfigPath `$ConfigPath
 }
 catch {
 Write-Warning "[TokenScout] Error: `$_"
 }
 Start-Sleep -Seconds `$Interval
}
"@

$Job = Start-Job -ScriptBlock ([scriptblock]::Create($ScoutCode)) -ArgumentList $TargetEndpoint, $IntervalSeconds -Name "TokenScout-$(Get-Random)"
Write-Host "[TokenScout] Started job $($Job.Id) for $TargetEndpoint"
return $Job
