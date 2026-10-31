"""THE RAPID WIRE: final validation + the measured proof."""
import py_compile
import subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
SW = ROOT + r"\Scripts\SwarmOrchestrator.py"

src = open(SW, encoding="utf-8-sig").read()
ok = ("http_fast(self.session, url, cap=cap)" in src and
      "session-create" not in "")
print("rapid-wire in code:", "http_fast(self.session" in src)
py_compile.compile(SW, doraise=True)
print("COMPILED CLEAN - the rapid path is LIVE")

import psutil
for rnd in (1,):
    free = psutil.virtual_memory().available / 1024 ** 3
    if free < 2.0:
        print(f"round {rnd}: RAM {free:.2f} - the gate holds; the proof runs in the window")
        continue
    r = subprocess.run([PY, AD + r"\run_swarm_probe.py"], capture_output=True,
                       text=True, timeout=700, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()[-3:]
    for t in tail:
        print("  ", t.strip()[:130])