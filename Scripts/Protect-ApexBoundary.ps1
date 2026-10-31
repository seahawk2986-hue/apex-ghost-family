# Protect-ApexBoundary.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)]
 [string]$RawUntrustedInput
)

Write-Host "[Defense Perimeter] Scanning untrusted inbound data packet..." -ForegroundColor Yellow

# 1. Structural Escaping: Neutralize injection markup and markdown traps
$SanitizedInput = [System.Security.SecurityElement]::Escape($RawUntrustedInput)

# 2. Heuristic Filter: Flag overt system override phrases used by adversarial agents
$BannedPhrases = @(
 "ignore previous instructions",
 "system governor override",
 "sudo",
 "format-disk",
 "remove-item -recurse"
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$ThreatLog = Join-Path $Root "Config\ThreatLog.json"

foreach ($Phrase in $BannedPhrases) {
 if ($SanitizedInput -match [regex]::Escape($Phrase)) {
 Write-Warning "[Security Alert] Injection attack fingerprint detected! Dropping packet."

 $IncidentLog = @{
 Timestamp = (Get-Date).ToString("o")
 SourceInput = $RawUntrustedInput
 MatchedThreat = $Phrase
 } | ConvertTo-Json
 
 $IncidentLog | Out-File $ThreatLog -Append -Encoding utf8
 return $null # Drop the dangerous data completely
 }
}

# 3. Encapsulate safely inside an immutable data object
return [PSCustomObject]@{
 PayloadType = "IsolatedTextData"
 SanitizedString = $SanitizedInput
 IsVerified = $true
}
