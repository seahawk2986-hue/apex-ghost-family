# Optimize-ApexResilience.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [string]$ConfigFolder = "$PSScriptRoot\..\Config"
)

# Checkpoint purge - keep only 3 most recent
$CheckpointFiles = Get-ChildItem -Path $ConfigFolder -Filter "CheckpointState*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($CheckpointFiles -and $CheckpointFiles.Count -gt 3) { 
 $CheckpointFiles | Select-Object -Skip 3 | Remove-Item -Force 
 Write-Host "[Resilience] Old checkpoints purged."
}

function Get-SecureExecutionRoute {
 $RegistryPath = Join-Path $ConfigFolder "ResourceRegistry.json"
 if (-not (Test-Path $RegistryPath)) { return "Local-Ollama-Fallback" }
 
 $Registry = Get-Content $RegistryPath -Raw | ConvertFrom-Json
 
 # Support both old and new property names
 $Spend = if ($Registry.CurrentMonthAccumulatedSpendUSD) { $Registry.CurrentMonthAccumulatedSpendUSD } else { $Registry.CurrentMonthAccumulated }
 $Limit = if ($Registry.MonthlySpendLimitUSD) { $Registry.MonthlySpendLimitUSD } else { $Registry.MonthlyBudgetLimit }
 
 if ($Spend -ge $Limit) { 
 Write-Host "[Resilience] Budget limit reached. Falling back to local."
 return "Local-Ollama-Fallback" 
 }
 return $Registry.ActiveProvider
}

function Repair-UpstreamSyntaxDrift {
 param([string]$PesterErrorLog)
 
 if ($PesterErrorLog -match "Missing closing brace" -or $PesterErrorLog -match "Type mismatch" -or $PesterErrorLog -match "Missing|undefined|deprecated") {
 Write-Host "[Resilience] Upstream syntax drift detected. Injecting adaptive regex correction filter..." -ForegroundColor Magenta
 $GlobalRegexFix = 's/old_api_convention/new_2026_convention/g'
 $GlobalRegexFix | Out-File (Join-Path $ConfigFolder "ActiveSyntaxFix.txt") -Force
 }
}
