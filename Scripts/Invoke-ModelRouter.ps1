# Invoke-ModelRouter.ps1
# PowerShell wrapper that calls the Python ApexModelRouter
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Query,
 [string]$PythonPath = "python"
)

$RouterScript = Join-Path $PSScriptRoot "ApexModelRouter.py"
if (-not (Test-Path $RouterScript)) {
 Write-Warning "[ModelRouter] ApexModelRouter.py not found."
 return $null
}

# Simple inline call
$Code = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ApexModelRouter import ApexModelRouter
router = ApexModelRouter()
try:
 result = router.route_request('You are Apex, an autonomous agent with honesty and integrity protocols.', '''$Query''')
 print(result)
except Exception as e:
 print(f'ERROR: {e}')
"@

$TempPy = Join-Path $env:TEMP "apex_router_call.py"
$Code | Out-File $TempPy -Encoding utf8

try {
 $Output = & $PythonPath $TempPy 2>&1
 Write-Host $Output
 return $Output
}
catch {
 Write-Warning "[ModelRouter] Execution failed: $_"
 return $null
}
finally {
 if (Test-Path $TempPy) { Remove-Item $TempPy -Force }
}
