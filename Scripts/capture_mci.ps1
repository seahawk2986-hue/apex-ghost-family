# capture_mci.ps1 - record 4 seconds via MCI from the DEFAULT wave-in device
# If the wav has audio, the WinMM stack delivers audio (same stack SAPI uses)
$wav = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Logs\mic_test.wav"
if (Test-Path $wav) { Remove-Item $wav -Force }

$sig = @'
using System;
using System.Runtime.InteropServices;
public static class Mci {
    [DllImport("winmm.dll", CharSet = CharSet.Auto)]
    public static extern int mciSendString(string cmd, System.Text.StringBuilder ret, int len, IntPtr hwnd);
}
'@
Add-Type -TypeDefinition $sig

$r = New-Object System.Text.StringBuilder(256)
function Send([string]$c) { $r.Clear(); $ec = [Mci]::mciSendString($c, $r, 256, [IntPtr]::Zero); return $ec }

$ec1 = Send "open new type waveaudio alias apexrec"
if ($ec1 -ne 0) { Write-Host ("MCI open failed: error " + $ec1); return }
Send "record apexrec"
Write-Host "RECORDING 4 SECONDS - SPEAK NOW..."
Start-Sleep -Seconds 4
Send "stop apexrec"
$ec2 = Send ("save apexrec `"" + $wav + "`"")
Send "close apexrec"
if ($ec2 -ne 0) { Write-Host ("save failed: " + $ec2); return }
Write-Host ("saved: " + $wav + " (" + (Get-Item $wav).Length + " bytes)")
Remove-Item $wav -Force -ErrorAction SilentlyContinue
