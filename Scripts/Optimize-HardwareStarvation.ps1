# Optimize-HardwareStarvation.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [string]$ProcessName = "powershell"
)

try {
 # Elevates priority class of active runspaces within Windows Kernel to protect old CPUs from lag
 Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | ForEach-Object {
 if ($_.PriorityClass -ne "High") { 
 $_.PriorityClass = "High" 
 Write-Host "[Hardware] Elevated priority for PID $($_.Id)"
 }
 }
}
catch {
 Write-Warning "[Hardware] Priority elevation failed: $_"
}
