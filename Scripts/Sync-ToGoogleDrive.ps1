# Sync-ToGoogleDrive.ps1
# Pushes key Apex folders to Google Drive (implements the persistence layer described)
[CmdletBinding()]
param(
 [string]$LocalRoot = "$PSScriptRoot\..",
 [string]$DriveFolderName = "Apex-Private"
)

Write-Host "[DriveSync] Preparing sync to Google Drive folder: $DriveFolderName"

# Create a clean export of the important state
$ExportPath = Join-Path $LocalRoot "DriveExport"
if (Test-Path $ExportPath) { Remove-Item $ExportPath -Recurse -Force }
New-Item -ItemType Directory -Path $ExportPath -Force | Out-Null

# Copy Config, Skills, and key scripts
$FoldersToSync = @("Config", "Skills")
foreach ($Folder in $FoldersToSync) {
 $Source = Join-Path $LocalRoot $Folder
 if (Test-Path $Source) {
 Copy-Item $Source (Join-Path $ExportPath $Folder) -Recurse -Force
 }
}

# Copy the main runner and sandbox file
Copy-Item (Join-Path $LocalRoot "AgentRunner.ps1") $ExportPath -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $LocalRoot "Launch-ApexSandbox.wsb") $ExportPath -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $LocalRoot "README.md") $ExportPath -Force -ErrorAction SilentlyContinue

Write-Host "[DriveSync] Export ready at $ExportPath"
Write-Host "[DriveSync] Use the Grok Drive tools or manual upload to push DriveExport/ contents."
return $ExportPath
