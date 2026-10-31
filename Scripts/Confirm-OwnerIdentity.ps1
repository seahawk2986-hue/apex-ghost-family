# Confirm-OwnerIdentity.ps1 - Master Root Developer Backdoor
[CmdletBinding()]
param()

$MasterDeveloperKey = "ApexDeveloper-Root"
if ($env:APEX_DEVELOPER_KEY -eq $MasterDeveloperKey) {
 Write-Host "[Security Perimeter] Owner Override Active"
 return $true
}
return $false
