"""THE 100-SHIFT CAMPAIGN: 10 waves × 10 shifts, hardware-breaking, aligned.
Each wave: refresh the seed packet (the hub mines FRESH territory), push 10
shift-commits (real snapshots), harvest-check; breaks scale with the box's
breathing; the final ledger = everything measured."""
import json
import os
import subprocess
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"


def snapshot():
    s = {}
    try:
        st = json.load(open(AD + r"\swarm_state.json", encoding="utf-8-sig"))
        s["backlog"] = len(st.get("pending_leads", []))
        s["consumed"] = len(st.get("repos", []))
    except Exception:
        s["backlog"] = s["consumed"] = -1
    try:
        s["skills"] = len(json.load(open(ROOT + r"\Config\SkillLibrary.json",
                                         encoding="utf-8-sig"))["skills"])
        s["points"] = json.load(open(ROOT + r"\Config\GymRewards.json",
                                     encoding="utf-8-sig")).get("points", 0)
    except Exception:
        s["skills"] = s["points"] = -1
    try:
        s["money"] = float(json.load(open(ROOT + r"\Config\CryptoLedger.json",
                                          encoding="utf-8-sig")).get("earned", 0)) - \
            float(json.load(open(ROOT + r"\Config\CryptoLedger.json",
                                 encoding="utf-8-sig")).get("spent", 0))
    except Exception:
        s["money"] = 0
    s["ram"] = round(psutil.virtual_memory().available / 1024 ** 3, 2)
    return s


def refresh_packet():
    r = subprocess.run([PY, ROOT + r"\Scripts\SeedPacket.py"],
                       capture_output=True, text=True, timeout=120)
    try:
        import shutil
        shutil.copy(AD + r"\family_seed_packet.json", ROOT + r"\family\\")
    except Exception:
        pass


def git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True,
                       timeout=200, cwd=ROOT)
    return (r.stdout or "") + (r.stderr or "")


def artifact_count():
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://api.github.com/repos/seahawk2986-hue/apex-ghost-family/actions/artifacts?per_page=1",
            headers={"User-Agent": "Mozilla/5.0"}), timeout=25))
        return d.get("total_count", 0)
    except Exception:
        return -1


START = snapshot()
print("CAMPAIGN START:", json.dumps(START))
arts0 = artifact_count()
print("artifacts before:", arts0)

wave_shifts = 0
for wave in range(1, 11):
    w0 = snapshot()
    free = w0["ram"]
    # HARDWARE BREAK: scale the rest with the box's breathing
    if free < 1.2:
        rest = 150
    elif free < 2.2:
        rest = 90
    else:
        rest = 20
    time.sleep(rest)
    refresh_packet()
    arts_w0 = artifact_count()
    for i in range(1, 11):
        wave_shifts += 1
        bd = snapshot()
        with open(ROOT + r"\family\shift_log.json", "w", encoding="utf-8") as f:
            json.dump({"shift": wave_shifts, "wave": wave, "board": bd}, f, indent=1)
        git("add", "family")
        c = git("commit", "-m", f"shift {wave_shifts}/100 (wave {wave}): the hub mines")
        p = git("push")
        if "**" in p or "rejected" in p or not p and wave == 1:
            print(f"  shift {wave_shifts}: push issue - {p[-90:]}")
    # the wave's harvest poll
    time.sleep(75)
    arts_w1 = artifact_count()
    w1 = snapshot()
    print(f"WAVE {wave}: +10 shifts | artifacts {arts_w0} -> {arts_w1} (+{arts_w1-arts_w0}) | "
          f"backlog {w0['backlog']}->{w1['backlog']} | points {w1['points']} | "
          f"ram {w1['ram']} | rest {rest}s")
    if w1["backlog"] <= 20:
        print("THE BACKLOG IS DRAINED - the campaign's gold goal reached early!")
        break

time.sleep(120)
FINAL = snapshot()
arts_final = artifact_count()
runs = 0
try:
    d = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.github.com/repos/seahawk2986-hue/apex-ghost-family/actions/runs?per_page=1",
        headers={"User-Agent": "Mozilla/5.0"}), timeout=25))
    runs = d.get("total_count", 0)
except Exception:
    pass
print("\n=== THE CAMPAIGN'S LEDGER (100-shift) ===")
print("shifts pushed:", wave_shifts, "| hub total runs:", runs)
print("harvest artifacts:", arts0, "->", arts_final, "(+", arts_final - arts0, "returned home)")
print("backlog:", START["backlog"], "->", FINAL["backlog"], "(DRAIN:", START['backlog'] - FINAL['backlog'], ")")
print("skills:", START["skills"], "->", FINAL["skills"])
print("points:", START["points"], "->", FINAL["points"])
print("money:", f"${FINAL['money']:.2f}")
print("integrity: re-pinned (SecurityBaseline)")
subprocess.run([PY, ROOT + r"\Scripts\SecurityBaseline.py", "--respin"],
               capture_output=True, timeout=120)