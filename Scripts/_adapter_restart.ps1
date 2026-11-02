# THE ADAPTER-RESTART (cull-then-start + health): the companion/engine pair
# reads the engine-source at boot, so the flip needs one clean restart.
$R = "C:\Users\seaha\Apex-Adapter"
$old = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'Apex-Adapter\\companion\.py' }
foreach ($o in $old) {
    Write-Host ("[culling adapter]: pid " + $o.ProcessId)
    try { Stop-Process -Id $o.ProcessId -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Seconds 2
Start-Process -FilePath "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\apex_venv\Scripts\python.exe" `
    -ArgumentList "$R\companion.py" -WorkingDirectory $R -WindowStyle Hidden
Start-Sleep -Seconds 8
$ok = $false
for ($i = 1; $i -le 4; $i++) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8788/v1/health" -TimeoutSec 6
        $ok = $true
        Write-Host ("[health]: ok, coding=" + $h.capabilities.coding.enabled)
        break
    } catch {
        Start-Sleep -Seconds 3
    }
}
if (-not $ok) { Write-Host "[VERDICT]: adapter did NOT come up"; exit 1 }
Get-Content "$R\Logs\adapter.log" -ErrorAction SilentlyContinue | Select-Object -Last 2