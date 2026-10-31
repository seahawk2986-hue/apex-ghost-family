# Invoke-SecureParallelTask.ps1 - Updated from Gemini thread
[CmdletBinding()]
param(
 [array]$TaskScriptBlocks,
 [int]$MaxExecutionTimeoutSeconds = 15
)

Write-Host "[Apex Velocity] Opening Secure Asynchronous Runspace Pools..." -ForegroundColor Yellow

$RunspacePool = [runspacefactory]::CreateRunspacePool(1, 4) # Cage allocation bound to 4 isolated threads
$RunspacePool.Open()

$Jobs = @()

foreach ($ScriptBlock in $TaskScriptBlocks) {
 $PowerShell = [PowerShell]::Create().AddScript($ScriptBlock)
 $PowerShell.RunspacePool = $RunspacePool
 
 $Jobs += [PSCustomObject]@{
 Pipe = $PowerShell
 Handle = $PowerShell.BeginInvoke()
 Timestamp = [System.Diagnostics.Stopwatch]::StartNew()
 }
}

# Track all running threads concurrently under strict temporal limits
foreach ($Job in $Jobs) {
 while (-not $Job.Handle.IsCompleted) {
 if ($Job.Timestamp.Elapsed.TotalSeconds -gt $MaxExecutionTimeoutSeconds) {
 Write-Warning "[Security Perimeter] Thread execution timeout tripped ($MaxExecutionTimeoutSeconds s). Terminating unresponsive background agent..."
 $Job.Pipe.Stop() # Hard kill the hanging process instantly
 break
 }
 Start-Sleep -Milliseconds 100
 }
}

$Results = foreach ($Job in $Jobs) {
 if ($Job.Handle.IsCompleted) {
 $Job.Pipe.EndInvoke($Job.Handle)
 }
 $Job.Pipe.Dispose()
}

$RunspacePool.Close()
$RunspacePool.Dispose()

return $Results
