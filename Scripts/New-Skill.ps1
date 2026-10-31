# New-Skill.ps1 - Further upgraded with research injection
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Request,
 [string]$SkillName = "GeneratedSkill"
)

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$SkillsPath = Join-Path $Root "Skills"
$StagingPath = Join-Path $SkillsPath "Staging"
$ScriptsPath = Join-Path $Root "Scripts"

if (-not (Test-Path $StagingPath)) { New-Item -ItemType Directory -Path $StagingPath -Force | Out-Null }

# Pull research insights if available
$Insights = @()
$ResearchScript = Join-Path $ScriptsPath "Get-ResearchInsights.ps1"
if (Test-Path $ResearchScript) {
 $Insights = & $ResearchScript -Topic $Request -MaxResults 2
}

$CodeHints = ($Insights | ForEach-Object { $_.CodeHint }) -join "`n# "

$Domain = "General"
if ($Request -match "finance|stock|portfolio|asset|risk") { $Domain = "Finance" }
if ($Request -match "log|analyze|parse") { $Domain = "LogAnalysis" }

$GeneratedCode = @"
# Auto-generated skill: $SkillName
# Domain: $Domain
# Request: $Request
# Research hints applied
[CmdletBinding()]
param()

try {
 Write-Host "[Skill:$SkillName] Starting ($Domain)..."
 
 # Research-informed skeleton
 # $CodeHints
 
 `$Result = @{
 Status = 'Ready'
 Domain = '$Domain'
 Request = '$Request'
 Generated = (Get-Date).ToString('o')
 Insights = $($Insights.Count)
 }
 
 Write-Host "[Skill:$SkillName] Completed successfully."
 return `$Result
}
catch {
 Write-Error "[Skill:$SkillName] Failed: `$_"
 return @{ Status = 'Failed'; Error = `$_.Exception.Message }
}
"@

$StagingFile = Join-Path $StagingPath "$SkillName.ps1"
$GeneratedCode | Out-File $StagingFile -Encoding utf8

# Validation gate
$Validator = Join-Path $ScriptsPath "Test-SkillIntegrity.ps1"
$Validation = & $Validator -SkillPath $StagingFile

if ($Validation.Passed) {
 $FinalPath = Join-Path $SkillsPath "$SkillName.ps1"
 Copy-Item $StagingFile $FinalPath -Force
 Write-Host "[SkillFactory] $SkillName validated and promoted."
 
 # Log
 $Log = Join-Path $Root "Config\SkillGenerationLog.json"
 $Entry = @{ Timestamp = (Get-Date).ToString("o"); Skill = $SkillName; Request = $Request; Status = "Promoted"; Insights = $Insights.Count }
 if (Test-Path $Log) {
 $Existing = Get-Content $Log -Raw | ConvertFrom-Json
 $Existing += $Entry
 $Existing | ConvertTo-Json -Depth 4 | Out-File $Log -Encoding utf8
 } else {
 @($Entry) | ConvertTo-Json -Depth 4 | Out-File $Log -Encoding utf8
 }
 return $true
}
else {
 Write-Warning "[SkillFactory] $SkillName failed validation: $($Validation.Failed -join ', ')"
 return $false
}
