# miccap.ps1 - record N seconds from a specific WinMM wave-in device via MCI.
param([int]$DevId, [string]$Out, [int]$Secs = 4)
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
function Send($c) { [Mci]::mciSendString($c, $r, 256, [IntPtr]::Zero) }
$ok1 = Send ("open new type waveaudio @" + $DevId + " alias rec" + $DevId)
if ($ok1 -ne 0) { Write-Host ("open failed for device " + $DevId + " (mciErr " + $ok1 + ")"); exit 1 }
Send ("record rec" + $DevId)
Start-Sleep -Seconds $Secs
Send ("stop rec" + $DevId)
$q = [char]34
$ok3 = Send ("save rec" + $DevId + " " + $q + $Out + $q)
if ($ok3 -ne 0) { Write-Host ("save failed (mciErr " + $ok3 + ")"); Send ("close rec" + $DevId); exit 1 }
Send ("close rec" + $DevId)
Write-Host ("recorded device " + $DevId + " -> " + $Out)