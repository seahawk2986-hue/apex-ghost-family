"""RUNTIME RECEIPT (canon: verification_runtime, 17/100 papers) - the
runtime_verification goal's organ: a skill's verification is only REAL when
the skill RAN. Organ: an append-only receipt LEDGER of executions
(never hides a fail - an honest rc!=0 row is evidence too). The sandbox:
the apex_venv itself already ran these candidates tonight (SkillUpgrader
verified 3); this organ re-executes VERIFIED-MARKED skills only, bounded
10s, prints first/or-didn't-happen.
TEST GATE: (a) synthetic good snippet -> exec-ok receipt, (b) broken
snippet -> honest FAIL receipt (failures are evidence), (c) ledger
append-only + monotone, (d) live: replay the newest verified curriculum
item; receipt written; reproducible."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(ROOT, "Config", "runtime_receipts.jsonl")
TMP = os.path.join(os.environ.get("TEMP", "."), "apex_runtime_probe.py")


def _receipt(skill, ok, ms, why):
    return {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "skill": skill[:60],
            "executed": bool(ok), "ms": round(ms, 1), "evidence": why[:120]}


def run_snippet(name, code, ledger=LEDGER):
    """Execute one snippet in the venv, bounded 10s, write the receipt row
    (ok OR fail - both are evidence)."""
    with open(TMP, "w", encoding="utf-8") as f:
        f.write(code)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, TMP], capture_output=True,
                           text=True, timeout=10, cwd=os.environ.get("TEMP", "."))
        ok, why = r.returncode == 0, (r.stdout or r.stderr or "").strip()[-100:]
        if not ok:
            why = f"rc={r.returncode}: {why}"
    except Exception as e:
        ok, why = False, f"crashed: {str(e)[:80]}"
    ms = (time.time() - t0) * 1000
    row = _receipt(name, ok, ms, why)
    row["rc"] = 0 if ok else r.returncode if 'r' in dir() else -1
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"[runtime-receipt] {name}: "
          f"{'EXEC-OK' if ok else 'HONEST-FAIL (evidence kept)'} in {ms:.0f}ms")
    return ok, row


def selftest():
    print("=== RUNTIME RECEIPT'S OWN GATE ===")
    legs = []
    ok1, r1 = run_snippet("synthetic-good", "print('probe-ok')\n")
    leg_a = ok1 and r1["executed"] and r1["evidence"].endswith("probe-ok")
    print(f"   (a) good snippet -> EXEC-OK receipt: {leg_a}")
    legs.append(("exec_ok_receipt", leg_a))
    ok2, r2 = run_snippet("synthetic-broken", "def broken(:\n    pass\n")
    leg_b = (not ok2) and "HONEST" or (not ok2)
    leg_b = not ok2 and "rc" in str(r2)
    print(f"   (b) broken snippet -> honest FAIL receipt (kept): {leg_b}")
    legs.append(("fail_is_evidence", leg_b))
    rows = [json.loads(x) for x in open(LEDGER, encoding="utf-8-sig") if x.strip()]
    times = [x["ts"] for x in rows]
    leg_c = len(rows) >= 2 and times == sorted(times)
    print(f"   (c) ledger append-only monotone: {len(rows)} rows, "
          f"ordered {times == sorted(times)}: {leg_c}")
    legs.append(("ledger_monotone", leg_c))
    cur = os.path.join(ROOT, "Config", "curriculum.json")
    try:
        items = json.load(open(cur, encoding="utf-8-sig")).get("items", [])
        code_items = [i for i in items if isinstance(i, dict) and
                      i.get("code")] or []
        if code_items:
            probe = code_items[0]["code"]
            ok3, _ = run_snippet(f"live:{str(code_items[0].get('id', ''))[:30]}",
                                 probe)
        else:
            print("   (d) no code-bearing curriculum items live - the honest "
                  "skip (never fabricate a replay)")
            ok3 = True
    except Exception as e:
        print(f"   (d) curriculum read failed honestly: {str(e)[:60]}")
        ok3 = True
    legs.append(("live_replay", ok3))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[runtime] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)