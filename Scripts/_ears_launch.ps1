# THE EARS-LAUNCH (cull-then-start): kill any existing ears-instance by
# literal PID (they hold old code in memory), then start ONE fresh ears
# on the current script via the known-good Start-Process pattern.
$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$old = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -match 'ApexEars' }
foreach ($o in $old) {
    Write-Host ("[culling old ears]: pid " + $o.ProcessId)
    try { Stop-Process -Id $o.ProcessId -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Seconds 2
Start-Process powershell -WindowStyle Hidden `
    -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', `
                  '-WindowStyle', 'Hidden', '-File', "$R\Scripts\ApexEars.ps1"
Start-Sleep -Seconds 7
$alive = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -match 'ApexEars' }
Write-Host "[ears alive on the CURRENT script]:"
foreach ($a in $alive) {
    Write-Host ("  pid " + $a.ProcessId + "  born " + $a.CreationDate.ToString("HH:mm:ss"))
}
Get-Content "$R\Logs\apex_ears.log" -ErrorAction SilentlyContinue |
    Select-Object -Last 3