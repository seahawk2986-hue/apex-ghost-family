# Protect-ApexScripts.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)][string]$ScriptPath,
 [switch]$GenerateSignature
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$ManifestFile = Join-Path $Root "Config\SecurityManifest.json"

if (-not (Test-Path $ManifestFile)) { 
 @{ FileHashes = @{} } | ConvertTo-Json | Out-File $ManifestFile -Force 
}

if (-not (Test-Path $ScriptPath)) {
 Write-Warning "[Integrity] Script not found: $ScriptPath"
 return $false
}

$CurrentHash = (Get-FileHash -Path $ScriptPath -Algorithm SHA256).Hash
$FileName = Split-Path $ScriptPath -Leaf
$Manifest = Get-Content $ManifestFile -Raw | ConvertFrom-Json

# Ensure FileHashes exists
if (-not $Manifest.FileHashes) {
 $Manifest | Add-Member -NotePropertyName FileHashes -NotePropertyValue @{} -Force
}

if ($env:APEX_DEVELOPER_KEY -eq "ApexDeveloper-RootAccess-2026" -or $GenerateSignature) {
 # Owner override or explicit signature generation
 $Manifest.FileHashes | Add-Member -NotePropertyName $FileName -NotePropertyValue $CurrentHash -Force
 $Manifest | ConvertTo-Json -Depth 10 | Out-File $ManifestFile -Force
 Write-Host "[Integrity] Signature updated for $FileName"
 return $true
}
else {
 $StoredHash = $Manifest.FileHashes.$FileName
 if ($null -eq $StoredHash -or $CurrentHash -ne $StoredHash) { 
 Write-Warning "[Integrity] Hash mismatch or missing for $FileName"
 return $false 
 }
 Write-Host "[Integrity] Hash verified for $FileName"
 return $true
}
