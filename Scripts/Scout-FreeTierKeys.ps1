# Scout-FreeTierKeys.ps1
# Legitimate free-tier discovery (official programs only, no leaked-key hunting)
[CmdletBinding()]
param(
 [string[]]$Services = @("OpenAI", "Anthropic", "GoogleAI", "Groq", "Together", "Ollama")
)

$FreeTierDirectory = @{
 "OpenAI" = @{ Url = "https://platform.openai.com/signup"; Note = "Free trial credits on new accounts" }
 "Anthropic" = @{ Url = "https://console.anthropic.com/"; Note = "Free tier available for Claude" }
 "GoogleAI" = @{ Url = "https://aistudio.google.com/"; Note = "Free Gemini API tier" }
 "Groq" = @{ Url = "https://console.groq.com/"; Note = "Free tier with rate limits" }
 "Together" = @{ Url = "https://api.together.xyz/"; Note = "Free credits on signup" }
 "Ollama" = @{ Url = "https://ollama.com/"; Note = "Fully local, no key required" }
 "HuggingFace"= @{ Url = "https://huggingface.co/settings/tokens"; Note = "Free inference API" }
}

$Results = @()
foreach ($Service in $Services) {
 if ($FreeTierDirectory.ContainsKey($Service)) {
 $Info = $FreeTierDirectory[$Service]
 $Results += [PSCustomObject]@{
 Service = $Service
 SignupUrl = $Info.Url
 Note = $Info.Note
 Status = "OfficialFreeTier"
 }
 Write-Host "[FreeTierScout] $Service -> $($Info.Url)"
 }
}

# Persist for Apex to reference
$Root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { Get-Location }
$OutPath = Join-Path $Root "Config\FreeTierDirectory.json"
$Results | ConvertTo-Json -Depth 3 | Out-File $OutPath -Encoding utf8

Write-Host "[FreeTierScout] Directory saved. Register manually and add keys to ResourceRegistry.json."
return $Results
