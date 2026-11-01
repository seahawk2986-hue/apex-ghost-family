"""THE 120B UTILIZATION'S LIVE RETEST (the test-then-retest law):
the QualityGate's REAL stage-3 through the wired ladder (groq-120b first)
on the capability-diff, x2 + the ensemble-retest + the honest rate-reading
(all receipts; $0.00 enforced)."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import QualityGate as QG
import CloudBrain as CB

DIFF_LINES = [
    "--- a/hooks/muse/provider_dummy.py",
    "+++ b/hooks/muse/provider_dummy.py",
    "@@ -1,3 +1,6 @@",
    " from pathlib import Path",
    " def load(p):",
    "-    return Path(p).read_text()",
    "+    p = Path(p)",
    "+    if not p.exists():",
    "+        raise FileNotFoundError(p)",
    "+    return p.read_text()",
]
DIFF = "\n".join(DIFF_LINES)
ISSUE = "the provider's load() should fail loudly on a missing file"
out = {"gate_reviews": [], "ensemble": None}

# T1: the stage-3 LIVE ladder x2
for i in range(2):
    r = QG.stage_brain_review(DIFF, ISSUE, "the 120b utilization retest")
    out["gate_reviews"].append(r)
    print(f"[retest T1.{i}] stage-3: ok={r.get('ok')} held={r.get('held')} "
          f"note={str(r.get('note'))[:70]}")
# T2: the ensemble w/ the ladder
try:
    import SkillForge as SF
    sc = SF.self_consistency('Reply ONLY the JSON {"sum": 7} (the sum of '
                             "3+4).", k=3, expect='{"sum": 7}')
    out["ensemble"] = sc
    print(f"[retest T2] ensemble: {sc.get('verdict')} agree="
          f"{sc.get('agree')}")
except Exception as e:
    out["ensemble"] = {"honest": str(e)[:80]}
# the receipt
ok = all(r.get("ok") for r in out["gate_reviews"])
with open(os.path.join(ROOT, "Config", "groq_120b_capability.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "retest": out,
               "verdict": "UTILIZED-2/2" if ok else "RETEST-CHECK",
               "model": "groq/openai/gpt-oss-120b", "local_ram_gb": 0.0,
               "cost": "$0.00"}, f, ensure_ascii=False, indent=1)
ens = (out.get("ensemble") or {}).get("agree", 0)
print(f"[retest] VERDICT: " + ("UTILIZED 2/2 (+ the ensemble vote)"
                               if ok and ens else "CHECK"))