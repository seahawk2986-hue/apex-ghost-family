# Initialize-ApexTriggers.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [string]$TargetFolder = "$PSScriptRoot\..\Config",
 [string]$TargetFile = "CurriculumQueue.txt"
)

Write-Host "[Event Trigger] Binding hardware-level FileSystemWatcher to Curriculum Queue..." -ForegroundColor Yellow

# 1. Instantiate the native .NET FileSystemWatcher API
$Watcher = New-Object System.IO.FileSystemWatcher
$Watcher.Path = $TargetFolder
$Watcher.Filter = $TargetFile
$Watcher.IncludeSubdirectories = $false
$Watcher.EnableRaisingEvents = $true

# 2. Define the immediate event trigger action block
$ActionBlock = {
 $EventName = $Event.SourceEventArgs.ChangeType
 Write-Host "[Hardware Event] Real-time file system modification spotted ($EventName). Awakening Apex Core..." -ForegroundColor Green
 
 # Fire the curriculum queue evaluation instantly
 $CurriculumScript = Join-Path $PSScriptRoot "Run-Curriculum.ps1"
 if (Test-Path $CurriculumScript) {
 & $CurriculumScript
 }
 else {
 Write-Warning "[Event Trigger] Curriculum script not found."
 }
}

# 3. Register the event monitor
$null = Register-ObjectEvent -InputObject $Watcher -EventName "Changed" -Action $ActionBlock

Write-Host "[Event Trigger] Watcher active. Press Ctrl+C to stop."
# Keep the session alive so the watcher stays registered
while ($true) { Start-Sleep -Seconds 5 }
