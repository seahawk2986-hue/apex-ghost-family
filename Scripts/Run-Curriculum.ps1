# Run-Curriculum.ps1 - Process CurriculumQueue.txt and generate skills
[CmdletBinding()]
param()

$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$QueuePath = Join-Path $Root "Config\CurriculumQueue.txt"
$ScriptsPath = Join-Path $Root "Scripts"

if (-not (Test-Path $QueuePath)) {
 Write-Warning "[Curriculum] Queue not found."
 return
}

$Tasks = Get-Content $QueuePath | Where-Object { $_ -match '\S' -and $_ -notmatch '^#' }

$i = 1
foreach ($Task in $Tasks) {
 $SkillName = "CurriculumSkill-$i"
 Write-Host "[Curriculum] Processing: $Task"
 
 $Success = & (Join-Path $ScriptsPath "New-Skill.ps1") -Request $Task -SkillName $SkillName
 
 if ($Success) {
 Write-Host "[Curriculum] Skill $i promoted."
 } else {
 Write-Warning "[Curriculum] Skill $i failed validation."
 }
 $i++
}

Write-Host "[Curriculum] Queue processed."
