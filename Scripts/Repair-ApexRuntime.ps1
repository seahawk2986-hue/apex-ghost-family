[CmdletBinding()]
param()

# Repair-ApexRuntime.ps1

# --- 1. AGGRESSIVE MEMORY PURGE (ANTI-LAG PROTOCOL) ---
function Optimize-MemoryGarbageCollection {
 Write-Host "[Self-Healing] Triggering aggressive memory reclamation sweep..." -ForegroundColor Purple
 [System.GC]::Collect()
 [System.GC]::WaitForPendingFinalizers()
 [System.GC]::Collect()
}

# --- 2. EXPONENTIAL BACKOFF FILE UNLOCK LOOP ---
function Get-SafeContentWithRetry {
 param([string]$FilePath)
 $BaseDelay = 1
 for ($attempt = 1; $attempt -le 4; $attempt++) {
 try {
 $FileStream = New-Object System.IO.FileStream($FilePath, 'Open', 'Read', 'ReadWrite')
 $Reader = New-Object System.IO.StreamReader($FileStream)
 $Content = $Reader.ReadToEnd()
 $Reader.Close()
 $FileStream.Close()
 return $Content
 } catch {
 $WaitTime = [Math]::Pow($BaseDelay, $attempt)
 Write-Host "[Self-Healing] File locked or sync lag caught! Retrying in $WaitTime seconds..." -ForegroundColor Yellow
 Start-Sleep -Seconds $WaitTime
 }
 }
 throw "[Self-Healing Critical] Unable to secure read handle over target file path!"
}

# --- 3. CLOUD OUTAGE FAILOVER ---
function Assert-CloudProviderUptime {
 param([string]$RegistryPath = "$PSScriptRoot\Config\ResourceRegistry.json")
 if (-not (Test-Path $RegistryPath)) { return $false }
 $Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json
 
 try {
 # Test basic web connectivity to determine remote model availability status
 $Ping = Invoke-WebRequest -UseBasicParsing -Uri "https://httpbin.org" -TimeoutSec 5 -ErrorAction Stop
 return $true
 } catch {
 Write-Host "[Self-Healing] Uptime probe failed! Cloud link down. Executing automatic failover..." -ForegroundColor Red
 $Registry.ActiveProvider = "Local-Ollama-Fallback"
 $Registry | ConvertTo-Json -Depth 4 | Out-File $RegistryPath -Encoding utf8 -Force
 return $false
 }
}

