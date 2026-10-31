# Cache-FailedRequests.ps1
param(
 [string]$TargetUri, 
 $FallbackCachePath = "C:\ApexCore\Config\OfflineFallbackCache.json"
)

try {
 # Perform a standard web query with basic content parameters
 $PingTest = Invoke-RestMethod -Uri "https://google.com" -Method Get -TimeoutSec 5 -ErrorAction Stop
 return $true
} 
catch {
 Write-Host "[Self-Healing] Web layer offline. Pulling fallback dataset..." -ForegroundColor Red
 if (Test-Path $FallbackCachePath) { return Get-Content $FallbackCachePath -Raw }
 return $null
}