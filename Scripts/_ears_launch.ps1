# THE EARS-LAUNCH (Start-Process edition): the known-good Windows detached
# pattern (python's DETACHED_PROCESS pops die instantly for SAPI hosts).
$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
Start-Process powershell -WindowStyle Hidden `
    -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', `
                  '-WindowStyle', 'Hidden', '-File', "$R\Scripts\ApexEars.ps1"
Start-Sleep -Seconds 7
$alive = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -match 'ApexEars' }
Write-Host "[ears alive]:"
foreach ($a in $alive) {
    Write-Host ("  pid " + $a.ProcessId + "  born " + $a.CreationDate.ToString("HH:mm:ss"))
}
Get-Content "$R\Logs\apex_ears.log" -ErrorAction SilentlyContinue |
    Select-Object -Last 3