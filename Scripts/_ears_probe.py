"""THE EARS BOOT-PROBE: run the (fixed) ApexEars.ps1 in the FOREGROUND for
12 seconds with output captured — a boot-crash reveals itself instantly;
a healthy boot listens silently until the timeout kills it."""
import os
import subprocess as sp

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)
try:
    r = sp.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", os.path.join(ROOT, "Scripts", "ApexEars.ps1")],
               capture_output=True, text=True, timeout=13,
               encoding="utf-8", errors="replace")
    print("[exit]:", r.returncode)
    print("[stdout-tail]:")
    for l in (r.stdout or "").splitlines()[-8:]:
        print("  ", l[:120])
    print("[stderr-tail]:")
    for l in (r.stderr or "").splitlines()[-8:]:
        print("  ", l[:150])
except sp.TimeoutExpired as e:
    print("[alive through the 13s probe (a healthy listen — the timeout = the kill)]")
    so = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    se = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
    print("[stdout-tail]:")
    for l in so.splitlines()[-6:]:
        print("  ", l[:120])
    print("[stderr-tail]:")
    for l in se.splitlines()[-6:]:
        print("  ", l[:150])