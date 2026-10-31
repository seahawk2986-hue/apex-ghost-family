# Start-ResourceDaemon.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [string]$ConfigPath = "$PSScriptRoot\..\Config\ResourceRegistry.json",
 [int]$ScanIntervalSeconds = 300
)

Write-Host "[Daemon] Initializing Continuous Free-Tier Discovery Service..." -ForegroundColor Cyan

while ($true) {
 try {
 if (Test-Path $ConfigPath) {
 $Registry = Get-Content $ConfigPath -Raw | ConvertFrom-Json
 
 foreach ($Pool in $Registry.Pools) {
 if ($Pool.QuotaRemaining -le 0 -and $Pool.ProviderName -ne "Local-Ollama-Fallback") {
 Write-Host "[Daemon] Quota exhausted for $($Pool.ProviderName). Suspending token." -ForegroundColor Yellow
 $Pool.Status = "Suspended"
 
 # Switch active provider if this was the active one
 if ($Registry.ActiveProvider -eq $Pool.ProviderName) {
 $Registry.ActiveProvider = "Local-Ollama-Fallback"
 Write-Host "[Daemon] Switched active provider to Local-Ollama-Fallback."
 }
 }
 }
 
 $Registry.LastDaemonScan = (Get-Date).ToString("o")
 $Registry | ConvertTo-Json -Depth 4 | Out-File $ConfigPath -Force -Encoding utf8
 }
 }
 catch {
 Write-Warning "[Daemon Error] Registry lock active. Retrying next cycle."
 }
 
 Start-Sleep -Seconds $ScanIntervalSeconds
}
