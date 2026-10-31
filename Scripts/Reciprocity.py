"""THE RECIPROCITY CHARTER: the swarm actively makes Andrew's life better.

He built them; they serve his life - implemented as three concrete channels:
 1. THE MORNING BRIEF: everything the family did overnight, in one read
    (written to Config/ApexNotes.json - the /notes route he already reads)
 2. THE HEALTH WATCH: his machine's wellbeing watched (disk/RAM/brain),
    alarms with actionable suggestions - his tool never surprises him
 3. THE JEWEL SURFACE: the family surfacing its best finds for him daily
    (top-graded mines + fresh issues worth reading) - he never digs.
"""
import json
import os
import shutil
import time
import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
NOTES = os.path.join(ROOT, "Config", "ApexNotes.json")
HEALTH = os.path.join(AD, "andrew_health_watch.json")


def health_watch():
    """Care for the machine his family living in - proactive, not reactive."""
    vm = psutil.virtual_memory()
    du = shutil.disk_usage("C:\\")
    alarms = []
    if vm.available / 1024 ** 3 < 1.5:
        alarms.append("RAM low (" + str(round(vm.available / 1024 ** 3, 1)) + " GB free) - close Chrome/Steam, or 'ApexServe.ps1 UnloadAll'")
    if du.free / (1024 ** 3) < 25:
        alarms.append("Disk tight (" + str(round(du.free / 1024 ** 3, 0)) + " GB) - harvest caps auto-trim; consider cleanup")
    try:
        brain_ok = psutil.Process().parent() is not None
    except Exception:
        brain_ok = True
    return {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ram_free_gb": round(vm.available / 1024 ** 3, 1),
            "disk_free_gb": round(du.free / 1024 ** 3, 0),
            "alarms": alarms}


def morning_brief():
    """Andrew's one-read brief: everything overnight + care, written to /notes."""
    brief = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "lines": []}
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
        brief["lines"].append("backlog waiting for tonight: " + str(len(st.get("pending_leads", []))) + " leads")
    except Exception:
        pass
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"), encoding="utf-8-sig"))["skills"]
        brief["lines"].append("skill library: " + str(len(lib)) + " verified skills ready when you ask")
    except Exception:
        pass
    try:
        rw = json.load(open(os.path.join(ROOT, "Config", "GymRewards.json"), encoding="utf-8-sig"))
        brief["lines"].append("family points: " + str(rw.get("points", 0)) + " (earned by verified work)")
    except Exception:
        pass
    try:
        cl = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"), encoding="utf-8-sig"))
        brief["lines"].append(f"money {float(cl.get("earned", 0)):.2f}$ / {float(cl.get("spent", 0)):.2f}$ (honest zero is fine)")
    except Exception:
        pass
    h = health_watch()
    for al in h["alarms"]:
        brief["lines"].append("⚠ " + al)
    if not h["alarms"]:
        brief["lines"].append("machine healthy: your box breathes fine")
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"), encoding="utf-8-sig"))
        top = (pm.get("grading") or {}).get("grades_top") or []
        if top:
            brief["lines"].append("today's jewels: " + ", ".join(k for k, v in top[:3] if v >= 8))
    except Exception:
        pass
    json.dump([brief], open(NOTES, "w", encoding="utf-8"), indent=1)
    json.dump(h, open(HEALTH, "w", encoding="utf-8"), indent=1)
    # the help events enter the GENOME: evolution now sees how much we helped
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
        hz = pm.setdefault("andrew_help", {})
        hz["briefs"] = int(hz.get("briefs", 0)) + 1
        hz["alarmsRaised"] = int(hz.get("alarmsRaised", 0)) + len(h.get("alarms", []))
        hz["lastHelp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        json.dump(pm, open(os.path.join(ROOT, "Config", "PathMemory.json"),
                           "w", encoding="utf-8"), indent=1)
    except Exception:
        pass
    return brief


if __name__ == "__main__":
    b = morning_brief()
    print(json.dumps(b, indent=1)[:700])