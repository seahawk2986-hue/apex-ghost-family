# Invoke-FastParallelTask.ps1 - RunspacePool parallel execution
[CmdletBinding()]
param(
 [scriptblock[]]$TaskScriptBlocks
)

$RunspacePool = [runspacefactory]::CreateRunspacePool(1, 10)
$RunspacePool.Open()
$Jobs = @()

foreach ($Block in $TaskScriptBlocks) {
 $PowerShell = [PowerShell]::Create()
 $PowerShell.RunspacePool = $RunspacePool
 $PowerShell.AddScript($Block)
 $Jobs += @{
 PS = $PowerShell
 Handle = $PowerShell.BeginInvoke()
 }
}

$Results = @()
foreach ($Job in $Jobs) {
 $Results += $Job.PS.EndInvoke($Job.Handle)
 $Job.PS.Dispose()
}

$RunspacePool.Close()
$RunspacePool.Dispose()
return $Results
