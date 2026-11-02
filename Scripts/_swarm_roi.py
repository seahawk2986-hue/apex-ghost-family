"""THE SWARM-ROI LEDGER: cost (wall-time, RAM-shape, $) vs the returns
(findings -> vetted skills -> score/points). The honest conversion-chain."""
import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADV = r"C:\Users\seaha\Apex-Adapter"
TODAY = "2026-11-01"

# the COST side
sw = json.load(open(os.path.join(ADV, "swarm_state.json"), encoding="utf-8-sig"))
runs = sw.get("runs", sw.get("n_runs")) or "?"
last = sw.get("last", {})
print("== COST ==")
print(f"[last run]: {sw.get('last_run')} | wall_s {last.get('wall_s')}"
      f" | findings+{last.get('findings')}")
print("[spend]: $0.00 (GitHub free quota; nothing paid, ever)")
ram_note = "[compute]: the farm/research = GitHub-Actions-runner-outsourced; local = the 72s-scans"

# the RETURNS side: findings count
fc = 0
fl = os.path.join(ADV, "swarm_findings.jsonl")
if os.path.exists(fl):
    fc = sum(1 for _ in open(fl, encoding="utf-8-sig", errors="ignore"))
print("\n== RETURNS (the pipeline) ==")
print(f"[findings lifetime]: {fc} (1228 claimed-by-state: {sw.get('findings')})")

# the score/points ledger
for cand in ("Config", r"..\Apex-Adapter"):
    for fn in ("score.json", "reward_score.json", "economy.json"):
        p = os.path.join(ROOT, cand, fn)
        if os.path.exists(p):
            print(f"[{cand}/{fn}]:", open(p, encoding="utf-8-sig").read()[:200])

# the reward-log today
rl = os.path.join(ROOT, "Logs", "reward.log")
if os.path.exists(rl):
    rows = open(rl, encoding="utf-8-sig", errors="ignore").readlines()
    trows = [l for l in rows if TODAY in l]
    print(f"[reward.log]: {len(trows)} rows today; the last 5:")
    for l in trows[-5:]:
        print("  ", l.strip()[:140])

# the skills-library (the real conversion)
sl = os.path.join(ROOT, "Scripts", "SkillLibrary.py")
if os.path.exists(sl):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "Scripts"))
    try:
        import SkillLibrary as SL
        lib = SL.load() or {}
        sk = lib.get("skills", [])
        vetted = [s for s in sk if s.get("sha256") or s.get("verified")]
        print(f"\n[skill-library]: {len(sk)} skills | vetted-with-sha: {len(vetted)}")
        for s in sk[-3:]:
            print(f"   {str(s.get('skill'))[:46]} <- {str(s.get('source_repo'))[:40]}")
    except Exception as e:
        print("[skill-library read]", str(e)[:80])
print(f"[{ram_note}]")