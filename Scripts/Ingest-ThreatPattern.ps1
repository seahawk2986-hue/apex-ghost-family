[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)]
 [object]$DroppedThreatObject
)

# Ingest-ThreatPattern.ps1
$DatabasePath = "$PSScriptRoot\..\Config\ThreatSignatures.json"
Write-Host "[Security Core] Reversing threat pattern structure..." -ForegroundColor Yellow

# Parse the structural signatures of the blocked attack string
$AttackText = $DroppedThreatObject.SourceInput
$DetectedVector = $DroppedThreatObject.MatchedThreat

# Extract specific regex or payload markers
$ExtractedPattern = ""
if ($AttackText -match "(?i)(system gov|override|ignore)") {
 $ExtractedPattern = $Matches[0]
}

# Load active threat database
if (Test-Path $DatabasePath) {
 $Database = Get-Content $DatabasePath -Raw | ConvertFrom-Json
} else {
 $Database = @{ Signatures = @() }
}

# Add structural signature metadata to database
$NewSignature = [PSCustomObject]@{
 Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
 AttackVectorType = "IndirectPromptInjection"
 ExtractedPattern = $ExtractedPattern
 ImmunizedStatus = "Active-Blocked"
}

$Database.Signatures += $NewSignature
$Database | ConvertTo-Json -Depth 5 | Out-File $DatabasePath -Encoding utf8 -Force
Write-Host "[Security Core] Threat neutralized and logged into Immunization Ledger." -ForegroundColor Green
