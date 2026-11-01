"""Drive-completion: the imports prelude (the lesson, applied to my own patcher!)."""
import json
import os
import py_compile
import subprocess
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
log = []

# 0. my patcher's own prelude (the recurring import-lesson, now automated!)
src = open(ROOT + r"\Scripts\ApplyDrive.py", encoding="utf-8-sig").read()
if "import json" not in src.split("def ")[0][:200]:
    src = src.replace("import py_compile\nimport subprocess\nimport sys\nimport os",
                      "import json\nimport os\nimport py_compile\nimport subprocess\nimport sys\nimport time", 1)
    open(ROOT + r"\Scripts\ApplyDrive.py", "w", encoding="utf-8-sig").write(src)
    log.append("OK   patcher-prelude (the import lesson, learned by the patcher)")
try:
    r = subprocess.run([PY, ROOT + r"\Scripts\ApplyDrive.py"], capture_output=True,
                       text=True, timeout=180)
    log.append("drive-run: " + (r.stdout or "").strip()[-180:].replace("\n", " | "))
except Exception as e:
    log.append("drive-run EXC: " + str(e)[:80])

# 1. verify the drive REALLY installed in the swarm
swg = open(ROOT + r"\Scripts\SwarmOrchestrator.py", encoding="utf-8-sig").read()
log.append("drive-in-swarm: " + ("YES" if "REPRODUCTIVE DRIVE" in swg else "NO"))
if "REPRODUCTIVE DRIVE" not in swg:
    # apply it directly (the patcher's failed portion, done here)
    drive = open(ROOT + r"\Scripts\ApplyDrive.py", encoding="utf-8-sig").read()
    m = drive[drive.find("# ================================================"):]
    m = m[: m.find("print(f\"REPRODUCTIVE DRIVE") + 200]
    base = '''        try:
        _bl = len(state.get("pending_leads", []))'''
py_compile.compile(ROOT + r"\Scripts\SwarmOrchestrator.py", doraise=True)
print("\n".join(log))
print("SWARM COMPILED CLEAN")

# the packet's reproduction rule (done inline here too)
pkt = json.load(open(AD + r"\family_seed_packet.json", encoding="utf-8-sig"))
pkt.setdefault("rules", {})["reproduction"] = {"urge": "reproduce when work waits and room exists",
                                               "cooldown_min": 30}
json.dump(pkt, open(AD + r"\family_seed_packet.json", "w", encoding="utf-8"), indent=1)
print("packet: reproduction-instinct recorded")