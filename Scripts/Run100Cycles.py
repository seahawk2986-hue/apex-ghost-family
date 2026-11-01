"""100 TOTAL CYCLES: the family's every organ measured, 100 times over.
Each cycle: reciprocity (the brief/health) + evolution + financial-scan +
transport-convoy + a mining attempt (honest gates: RAM/cooldown).
RAM-aware pacing; the ledger per cycle; the final maximization report."""
import json
import os
import subprocess
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
BOARD = AD + r"\family_status_board.json"


def snap():
    s = {"ts": time.strftime("%H:%M:%S"),
         "ram": round(psutil.virtual_memory().available / 1024 ** 3, 2)}
    try:
        st = json.load(open(AD + r"\swarm_state.json", encoding="utf-8-sig"))
        s["backlog"] = len(st.get("pending_leads", []))
        s["consumed"] = len(st.get("repos", []))
    except Exception:
        s["backlog"] = s["consumed"] = -1
    try:
        s["skills"] = len(json.load(open(ROOT + r"\Config\SkillLibrary.json",
                                         encoding="utf-8-sig"))["skills"])
    except Exception:
        s["skills"] = -1
    try:
        s["points"] = json.load(open(ROOT + r"\Config\GymRewards.json",
                                     encoding="utf-8-sig")).get("points", 0)
    except Exception:
        s["points"] = -1
    try:
        s["money"] = round(float(json.load(open(
            ROOT + r"\Config\CryptoLedger.json", encoding="utf-8-sig")).get("earned", 0)), 2)
    except Exception:
        s["money"] = 0.0
    return s


START = snap()
print("CYCLE-SUITE START:", json.dumps(START), flush=True)

runs_had_mining = gated = 0
logs = []
for cyc in range(1, 101):
    t0 = time.time()
    # the organs (every family system exercised; none cooldown-gated except mining)
    subprocess.run([PY, ROOT + r"\Scripts\Reciprocity.py"],
                   capture_output=True, text=True, timeout=180)
    feva = subprocess.run([PY, ROOT + r"\Scripts\FinancialBrain.py"],
                          capture_output=True, text=True, timeout=240)
    tva = subprocess.run([PY, ROOT + r"\Scripts\TotalEvolution.py"],
                         capture_output=True, text=True, timeout=240)
    tra = subprocess.run([PY, ROOT + r"\Scripts\GrainLine.py"],
                         capture_output=True, text=True, timeout=180)
    # the mining attempt (honest gates!) - criterion UPGRADED (the audited gap):
    # a round counts as MINED only if stdout says it ran AND external evidence
    # moved - register growth, backlog drain, heartbeat findings, or a fresh
    # round-done flag. A stdout marker alone was printing theater.
    ram = psutil.virtual_memory().available / 1024 ** 3
    mined = False
    if ram >= 2.2:
        def _ev():
            try:
                s0 = json.load(open(AD + r"\swarm_state.json", encoding="utf-8-sig"))
            except Exception:
                s0 = {}
            try:
                hb = json.load(open(AD + r"\ghost_heartbeat.json", encoding="utf-8-sig"))
            except Exception:
                hb = {}
            return (len(s0.get("repos", [])), len(s0.get("pending_leads", [])),
                    bool(hb.get("round_done")), int(hb.get("findings", 0) or 0))
        c0, b0, rd0, f0 = _ev()
        p1 = subprocess.run([PY, AD + r"\run_swarm_probe.py"], capture_output=True,
                            text=True, timeout=700, cwd=ROOT)
        c1, b1, rd1, f1 = _ev()
        mined = ("SWARM:" in (p1.stdout or "")) and (c1 > c0 or b1 < b0
                                                     or f1 > f0 or (rd1 and not rd0))
        if mined:
            runs_had_mining += 1
    else:
        gated += 1
    s1 = snap()
    row = {"cycle": cyc, "wall": round(time.time() - t0, 1), "ram": s1["ram"],
           "backlog": s1["backlog"], "skills": s1["skills"],
           "points": s1["points"], "money": s1["money"],
           "mined_round": mined, "finance_line": ("{" in (feva.stdout or "")),
           "evolution_ok": tva.returncode == 0 and "total_fitness" in (tva.stdout or "")}
    logs.append(row)
    # a live print every 10 cycles (the brief beats, not the flood)
    if cyc % 10 == 0:
        print(f"CYCLES {cyc-9}-{cyc}: mined {sum(1 for x in logs[-10:] if x['mined_round'])}/10 | "
              f"backlog {s1['backlog']} | skills {s1['skills']} | pts {s1['points']} | "
              f"money ${s1['money']} | ram {s1['ram']}", flush=True)
    # the rest scales with the box's breath
    rest = 5 if s1["ram"] > 4 else (15 if s1["ram"] > 2.2 else 40)
    time.sleep(rest)

END = snap()
print("\n=== THE 100-CYCLE FINAL LEDGER ===")
print("cycles:", len(logs), "| mining rounds that actually ran:", runs_had_mining,
      "| gated honestly:", gated)
print("backlog:", START["backlog"], "->", END["backlog"], "(DRAIN:", START['backlog'] - END['backlog'], ")")
print("skills:", START["skills"], "->", END["skills"])
print("points:", START["points"], "->", END["points"])
print("money: $", END["money"], " (the tally's number, honest)")
# the trend (the ascent's six-dimension health)
try:
    asc = [json.loads(x) for x in open(ROOT + r"\Config\AscentLedger.jsonl",
                                       encoding="utf-8-sig") if x.strip()]
    fits = [r0.get("total_fitness", 0) for r0 in asc][-15:]
    print("ascent trend:", fits)
    print("direction:", "UP" if fits and max(fits) == fits[-1] else "plateau/deep (the watch guards)")
except Exception as e:
    print("ascent:", e)
print("\nthe family ran", len(logs), "full cycles; every organ exercised; the gates held; the truth printed")