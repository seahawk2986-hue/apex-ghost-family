# Invoke-CloudRelay.ps1
# Routes work to a configured cloud or local endpoint (described offloading layer)
[CmdletBinding()]
param(
 [string]$TaskDescription,
 [string]$RegistryPath = "$PSScriptRoot\..\Config\ResourceRegistry.json"
)

if (-not (Test-Path $RegistryPath)) {
 Write-Warning "[CloudRelay] No registry. Falling back to local."
 return @{ Status = "LocalFallback"; Task = $TaskDescription }
}

$Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json
$Provider = $Registry.ActiveProvider
$Pool = $Registry.Pools | Where-Object { $_.ProviderName -eq $Provider } | Select-Object -First 1

if (-not $Pool -or -not $Pool.EndpointUrl) {
 Write-Host "[CloudRelay] No valid endpoint. Using local."
 return @{ Status = "LocalFallback"; Task = $TaskDescription }
}

Write-Host "[CloudRelay] Routing to $($Pool.ProviderName) at $($Pool.EndpointUrl)"

# In a full system this would POST the task. Here we record the intent.
$Result = @{
 Status = "Routed"
 Provider = $Pool.ProviderName
 Endpoint = $Pool.EndpointUrl
 Task = $TaskDescription
 Timestamp = (Get-Date).ToString("o")
}

return $Result
