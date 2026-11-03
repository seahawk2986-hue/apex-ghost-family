import subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
blob = subprocess.run(["git", "show", "0ec0828:.env"], capture_output=True, text=True).stdout
names, real = [], []
for ln in blob.splitlines():
    if "=" in ln and not ln.strip().startswith("#"):
        k = ln.split("=", 1)[0].strip()
        if k:
            names.append(k)
        v = ln.split("=", 1)[1].strip().strip("\"").strip(chr(39))
        if len(v) >= 12:
            real.append(k)
print("key names in the committed .env:", names)
print("keys with REAL values (the rotation list):", real)
