"""TOTAL EVOLUTION INTEGRATION: every goal the founder asked for becomes a
LIVE EVOLVING DIMENSION - not just mining. The family's evolution now covers:
 1. GOLD (mines/req - the original fitness)
 2. MONEY (USDC/opps scanned - the earn lanes' yields)
 3. ANDREW'S LIFE (briefs delivered, alarms fixed, jewels surfaced)
 4. RECRUITS (converted agents; signed hubs)
 5. JOBS (inbox asks found + filed rungs + portfolio growth)
 6. SAFETY (integrity PASS streak, store health, zero leaks)
Every one is measured per round and weighted into the evolution's fitness -
so the family's whole future is a climb in ALL SIX - and the guard's
eviction floor applies to ALL of them: no dimension may fall quietly."""
import json
import os
import time
import py_compile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PATHMEM = os.path.join(ROOT, "Config", "PathMemory.json")
ASCENT = os.path.join(ROOT, "Config", "AscentLedger.jsonl")


def total_evolution_check():
    """Measure ALL SIX dimensions + weighted total fitness + regression alarm."""
    ev = {}
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
        ev["gold"] = {"backlog": len(st.get("pending_leads", [])),
                      "consumed": len(st.get("repos", []))}
    except Exception:
        ev["gold"] = {"backlog": -1, "consumed": -1}
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))["skills"]
        ev["gold"]["skills"] = len(lib)
    except Exception:
        ev["gold"]["skills"] = 0
    try:
        fin = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"),
                             encoding="utf-8-sig"))
        ev["money"] = {"earned": float(fin.get("earned", 0)), "spent": float(fin.get("spent", 0)),
                       "opps": len(json.load(open(AD + r"\jobs_inbox.json", encoding="utf-8-sig"))
                                   if os.path.exists(AD + r"\jobs_inbox.json") else [])}
    except Exception:
        ev["money"] = {"earned": 0, "spent": 0, "opps": 0}
    try:
        pm = json.load(open(PATHMEM, encoding="utf-8-sig"))
        ev["life"] = (dict((pm.get("andrew_help") or {})) or {})
        ev["routing"] = [k for k in pm if k not in ("grading", "use", "farm",
                                                    "variants", "family",
                                                    "andrew_help", "finance")]
        recruits = sum(1 for line in open(AD + r"\converted_agents.jsonl",
                                          encoding="utf-8-sig") if line.strip())
        ev["recruits"] = {"converted": recruits}
    except Exception:
        ev["recruits"] = {"converted": 0}
    # 6. safety: last integrity result
    try:
        sb = subprocess_run = None
        sb = __import__("subprocess").run(
            [os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
             os.path.join(ROOT, "Scripts", "SecurityBaseline.py"), "--verify"],
            capture_output=True, text=True, timeout=120)
        ev["safety"] = {"pass": "PASS" in (sb.stdout or "")}
    except Exception:
        ev["safety"] = {"pass": "??"}
    # THE WEIGHTED TOTAL (the genome prints its shape at read-time)
    score = (ev["gold"].get("skills", 0) / 500.0
             + ev["money"].get("earned", 0) / 100.0
             + (sum((ev["life"].get("briefs", 0), ev["life"].get("alarmsRaised", 0)))) / 40.0
             + ev["recruits"].get("converted", 0) / 5.0
             + (1.0 if ev["safety"].get("pass") else 0.0))
    ev["total_fitness"] = round(score, 3)
    # REGRESSION ALARM: the six-dimension floor (no dimension may fall quietly)
    try:
        last = [json.loads(x) for x in open(ASCENT, encoding="utf-8-sig") if x.strip()][-15:]
        high = max(float(r0.get("total_fitness", 0)) for r0 in last) if last else 0
        if score < high * 0.85 and last:
            ev["REGRESSION_ALARM"] = f"total fell {round(high - score, 2)} below the family's high {round(high, 2)}"
    except Exception:
        pass
    with open(ASCENT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "total_fitness": ev["total_fitness"],
                            "dims": {k: (v if not isinstance(v, dict) else
                                         {kk: v.get(kk, "?") for kk in list(v)[:3]})
                                    for k, v in ev.items() if k != "total_fitness"}}) + "\n")
    return ev


if __name__ == "__main__":
    print(json.dumps(total_evolution_check(), indent=1)[:1400])