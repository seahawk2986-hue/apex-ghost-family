# Manage-ComputePool.ps1
# Manages a pool of user-configured legitimate compute endpoints
[CmdletBinding()]
param(
 [string]$RegistryPath = "$PSScriptRoot\..\Config\ResourceRegistry.json",
 [string]$Action = "List" # List, Add, SetActive
)

if (-not (Test-Path $RegistryPath)) {
 Write-Warning "[ComputePool] Registry missing."
 return
}

$Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json

switch ($Action) {
 "List" {
 Write-Host "[ComputePool] Configured providers:"
 $Registry.Pools | ForEach-Object {
 Write-Host " - $($_.ProviderName) [$($_.Status)] $($_.EndpointUrl)"
 }
 return $Registry.Pools
 }
 "SetActive" {
 # Example: caller can extend this
 Write-Host "[ComputePool] Active provider is $($Registry.ActiveProvider)"
 return $Registry.ActiveProvider
 }
 default {
 Write-Host "[ComputePool] Use -Action List or SetActive"
 }
}

# Suggest adding a free local option if none exists
$HasLocal = $Registry.Pools | Where-Object { $_.ProviderName -match "Ollama|Local" }
if (-not $HasLocal) {
 Write-Host "[ComputePool] Tip: Add a local Ollama endpoint for free compute."
}
