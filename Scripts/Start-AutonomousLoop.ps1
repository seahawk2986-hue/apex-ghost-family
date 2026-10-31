# Start-AutonomousLoop.ps1
# Launches the Python ApexAutonomousAgent loop
[CmdletBinding()]
param(
 [string]$PythonPath = "$PSScriptRoot\..\apex_venv\Scripts\python.exe"
)

$AgentScript = Join-Path $PSScriptRoot "ApexAutonomousAgent.py"
if (-not (Test-Path $AgentScript)) {
 Write-Warning "[Autonomous] ApexAutonomousAgent.py not found."
 return
}

Write-Host "[Autonomous] Starting Apex autonomous loop (Ctrl+C to stop)..."
& $PythonPath $AgentScript
