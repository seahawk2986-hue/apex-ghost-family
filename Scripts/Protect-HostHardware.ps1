# Protect-HostHardware.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [int]$MaxAllowedCpu = 75
)

try {
 $CpuLoad = (Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object -Property LoadPercentage -Average).Average
}
catch {
 $CpuLoad = 0
}

if ($CpuLoad -gt $MaxAllowedCpu) {
 Write-Host "[Thermal Guard] Resource constraint hit ($CpuLoad%). Throttling down execution layers..." -ForegroundColor Yellow
 Start-Sleep -Seconds 10
 return $false
}

return $true
