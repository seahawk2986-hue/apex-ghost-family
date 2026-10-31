# Compress-ResearchContext.ps1 - Speculative abstract filter
[CmdletBinding()]
param(
 [string]$RawResearchText
)

# Strip non-operational text, keep methods, results, code
$Lines = $RawResearchText -split "`n"
$Operational = $Lines | Where-Object {
 $_ -match "function |param |return |# |algorithm|method|result|implementation"
}

return ($Operational -join "`n")
