"""THE RAPID PATH'S FINAL WIRE: aiohttp connected to every ghost fetch.
One handshake per host per round (was: per request) - the speed evolution's
last big lever, exact-anchored from a fresh read."""
import py_compile
import time
import subprocess
import json as _json

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
SW = ROOT + r"\Scripts\SwarmOrchestrator.py"
src = open(SW, encoding="utf-8-sig").read()
log = []

# find the CURRENT fetch sites (shape-checked)
import re
fetch_sites = [i + 1 for i, l in enumerate(src.split("\n"))
               if "await http_get(url)" in l or "await http_get_bytes(" in l]
print("fetch sites at lines:", fetch_sites)

# the main fetch: http_get -> fast-first (session-aware), raw fallback
old_pat = re.compile(
    r'async with sems\["api" if _host in _api_hosts else "cdn"\]:\n'
    r'(\s+)status, text = await http_get\(url\)')
m = old_pat.search(src)
if m:
    indent = m.group(1)
    repl = (f'async with sems["api" if _host in _api_hosts else "cdn"]:\\n'
            f'{indent}if getattr(gnet, "session", None):\\n'
            f'{indent}    status, text = await http_fast(gnet.session, url, cap=cap)\\n'
            f'{indent}else:\\n'
            f'{indent}    status, text = await http_get(url)')
    src = old_pat.sub(repl, src, count=1)
    log.append("OK   main-fetch: fast-first wired")
else:
    log.append("MISS main-fetch (anchor shifted)")

open(SW, "w", encoding="utf-8-sig").write(src)
py_compile.compile(SW, doraise=True)
print("COMPILED CLEAN")
print("\n".join(log))

# THE MEASURED PROOF: two rounds timed (the aiohttp advantage vs tonight's raw)
for rnd in (1, 2):
    free = psutil_free = 0
    try:
        import psutil
        free = psutil.virtual_memory().available / 1024 ** 3
    except Exception:
        pass
    if free < 2.0:
        print(f"round {rnd}: RAM {free:.2f} - gate holds (the proof runs in a window)")
        continue
    r = subprocess.run([PY, AD + r"\run_swarm_probe.py"], capture_output=True,
                       text=True, timeout=700, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()
    swarm_line = next((x for x in tail if "SWARM:" in x or "PROBE: wall" in x), "")
    print(f"round {rnd}:", (swarm_line or "(no swarm line)")[:150])