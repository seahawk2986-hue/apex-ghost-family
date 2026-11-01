"""ApexMicProbe - differential mic test: per-device 4 s MCI capture + RMS.

Instructs Andrew out loud first (ApexSpeak), records each wave-in device,
classifies silent vs audio. Answers: does the Kraken carry audio, and which
device is WinMM's default actually hearing?"""
import ctypes
import ctypes.wintypes as wt
import math
import os
import struct
import subprocess
import sys
import wave

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
CAP = os.path.join(REPO, "Scripts", "miccap.ps1")
TMP = os.path.join(REPO, "Logs")

# --- enumerate WinMM wave-in devices -----------------------------------------
winmm = ctypes.windll.winmm


class WAVEINCAPSW(ctypes.Structure):
    _fields_ = [("wMid", wt.WORD), ("wPid", wt.WORD),
                ("vDriverVersion", wt.DWORD),
                ("szPname", wt.WCHAR * 32),
                ("dwFormats", wt.DWORD), ("wChannels", wt.WORD),
                ("wReserved1", wt.WORD)]


n = winmm.waveInGetNumDevs()
devices = []
for i in range(n):
    caps = WAVEINCAPSW()
    rc = winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps))
    if rc == 0:
        devices.append((i, caps.szPname))
print("wave-in devices:")
for i, name in devices:
    print(f"  [{i}] {name}")

# --- tell Andrew out loud to speak during capture -----------------------------
subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", os.path.join(REPO, "Scripts", "ApexSpeak.ps1"),
                "-Message",
                "Andrew, say Apex status check three times right now, clearly."],
               timeout=60)

results = []
for i, name in devices:
    out = os.path.join(TMP, f"mic_dev{i}.wav")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", CAP, "-DevId", str(i), "-Out", out, "-Secs", "4"],
                       capture_output=True, text=True, timeout=90)
    line = (r.stdout or r.stderr or "").strip().splitlines()
    line = line[-1] if line else "no output"
    rms = None
    if os.path.exists(out):
        try:
            with wave.open(out, "rb") as w:
                frames = w.readframes(w.getnframes())
                width = w.getsampwidth()
                nfr = w.getnframes()
            if width == 2:
                samples = struct.unpack(f"<{len(frames)//2}h", frames)
                acc = 0.0
                for s in samples:
                    acc += float(s) * float(s)
                rms = math.sqrt(acc / max(1, len(samples)))
        except Exception as e:
            print(f"  [{i}] {name}: wav unreadable: {e}")
        size = os.path.getsize(out)
    else:
        size = 0
    verdict = "NO DATA" if rms is None else (
        "SILENT (rms %.1f)" % rms if rms < 20 else "AUDIO! (rms %.1f)" % rms)
    print(f"  [{i}] {name}: {verdict} | mci: {line} | bytes {size}")
    results.append((i, name, rms))

ok = [r for r in results if r[2] is not None and r[2] >= 20]
print()
if ok:
    print("VERDICT: audio heard on device(s): " +
          ", ".join(f"[{i}] {name}" for i, name, _ in ok))
    print("=> set that device as Windows default input OR we aim SAPI at it.")
else:
    print("VERDICT: NO device captured speech - mic muted/level-zero/exclusive, "
          "or headset hands-free mic off in Windows sound settings.")