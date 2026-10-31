# Get-AcademicInsights.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [Parameter(Mandatory = $true)][string]$TopicKeywords
)

$EncodedQuery = [uri]::EscapeDataString($TopicKeywords)
$Uri = "http://export.arxiv.org/api/query?search_query=all:$EncodedQuery&max_results=2"

try {
 $Feed = Invoke-RestMethod -Uri $Uri -Method Get -TimeoutSec 15
 $Insights = @()
 
 foreach ($Entry in $Feed.feed.entry) {
 $Abstract = $Entry.summary.Trim()
 $Keywords = @()
 
 if ($Abstract -match "asynchronous|parallel") { $Keywords += "ParallelExecution" }
 if ($Abstract -match "matrix|vector") { $Keywords += "DotNetArrays" }
 if ($Abstract -match "optimization|gradient") { $Keywords += "Optimization" }
 if ($Abstract -match "neural|transformer|llm") { $Keywords += "NeuralModels" }
 
 $Insights += [PSCustomObject]@{
 Title = $Entry.title.Trim()
 AbstractSnippet = if ($Abstract.Length -gt 200) { $Abstract.Substring(0, 200) + "..." } else { $Abstract }
 DesignDirectives = $Keywords
 }
 }
 
 # Cache the insights
 $Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
 $CachePath = Join-Path $Root "Config\ResearchCache.json"
 $Entry = @{
 Topic = $TopicKeywords
 Timestamp = (Get-Date).ToString("o")
 Insights = $Insights
 }
 
 if (Test-Path $CachePath) {
 $Existing = Get-Content $CachePath -Raw | ConvertFrom-Json
 $Existing += $Entry
 $Existing | ConvertTo-Json -Depth 6 | Out-File $CachePath -Encoding utf8
 }
 else {
 @($Entry) | ConvertTo-Json -Depth 6 | Out-File $CachePath -Encoding utf8
 }
 
 Write-Host "[Research] Retrieved $($Insights.Count) insights for '$TopicKeywords'."
 return $Insights
}
catch {
 Write-Warning "[Research] arXiv fetch failed: $($_.Exception.Message)"
 return $null
}
