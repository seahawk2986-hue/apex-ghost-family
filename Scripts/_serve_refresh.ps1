# THE SERVE-REFRESH: the single clean restart that loads the
# prose-vocabulary prompt (the vocab-parity law, server-side).
# Cull by literal PID -> Start-Process detached -> 26s settle -> proof.
$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$old = Get-CimInstance Win32_Process |
    Where-Object {
        ("python" -eq ($_.Name -replace '\.exe', '').ToLower() -or
         "python" -like $_.Name) -and
        $_.CommandLine -match 'run_apex_evolution\.py' }
foreach ($o in $old) {
    Write-Host ("[culling serve]: pid " + $o.ProcessId)
    try { Stop-Process -Id $o.ProcessId -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Seconds 3
Start-Process -FilePath "$R\apex_venv\Scripts\python.exe" `
    -ArgumentList "$R\run_apex_evolution.py" -WorkingDirectory $R `
    -WindowStyle Hidden
Write-Host "[serve relaunched detached]; settling 26s..."
Start-Sleep -Seconds 26
$ok = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $st = Invoke-RestMethod -Uri "http://127.0.0.1:8080/talk/status" -TimeoutSec 6
        $ok = $true
        Write-Host "[status]: HTTP-ok"
        break
    } catch {
        Write-Host ("[status] try " + $i + ": waiting...")
        Start-Sleep -Seconds 4
    }
}
if (-not $ok) {
    Write-Host "[VERDICT]: serve did NOT come up - honest fail, no fake green"
    exit 1
}
$key = (Get-Content "$R\Config\apex_api.key" -Raw).Trim()
$rep = Invoke-RestMethod -Uri "http://127.0.0.1:8080/talk/api" -Method Post `
    -ContentType "application/json" -Headers @{ "X-Apex-Key" = $key } `
    -Body (@{ message = "Say two sentences about what you are, spoken style." } | ConvertTo-Json -Compress) `
    -TimeoutSec 90
$txt = [string]$rep.reply
$md = ($txt -match '##') -or ($txt -match '\*\*')
Write-Host ("[reply len]: " + $txt.Length + " chars | [markdown noise]: " + $md)
Write-Host ("[reply head]: " + $txt.Substring(0, [Math]::Min(140, $txt.Length)))
Get-Content "$R\Logs\system.log" -ErrorAction SilentlyContinue | Select-Object -Last 2