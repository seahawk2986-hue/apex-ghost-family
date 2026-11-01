"""THE RUNNER-PORTABLE TEST (the workflow's real proof): a simulated
runner tree (the repo's layout: Scripts + Config + the adapter files)
with APEX_ROOT/APEX_ADAPTER pointing INTO it - the organs must run there
(the outsource condition) and write their receipts THERE."""
import json
import os
import re
import shutil
import subprocess
import sys

from collections import OrderedDict

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
SIM = os.path.join(os.environ.get("TEMP", "."), "runner_sim")
os.makedirs(os.path.join(SIM, "Scripts"), exist_ok=True)
os.makedirs(os.path.join(SIM, "Config"), exist_ok=True)
# the layout pieces
for f in ("ClaimCheck.py", "EarnLaneMatrix.py", "EarnNowPipeline.py",
          "PatchStep.py", "SafeIO.py"):
    src = os.path.join(ROOT, "Scripts", f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(SIM, "Scripts", f))
for f in ("file_now_kit.json", "gh_archive_bugs.jsonl", "jobs_inbox.json",
          "service_catalog.json", "goldmine_register.json"):
    src = os.path.join(AD, f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(SIM, f))
for f in ("CryptoLedger.json", "papers_2026_earning.jsonl"):
    src = os.path.join(ROOT, "Config", f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(SIM, "Config", f))
shutil.copy(os.path.join(ROOT, "Config", "papers_2026_earning.jsonl"),
            os.path.join(SIM, "Config", "papers_2026_earning.jsonl"))
env = dict(os.environ)
env["APEX_ROOT"] = SIM
env["APEX_ADAPTER"] = SIM
r1 = subprocess.run([sys.executable, os.path.join(SIM, "Scripts",
                     "EarnLaneMatrix.py")], capture_output=True, text=True,
                    timeout=900, env=env)
ok1 = r1.returncode == 0 and os.path.exists(os.path.join(
    SIM, "earn_lane_matrix.json"))
print("the matrix in the sim tree:", "PASS" if ok1 else
      ("FAIL: " + (r1.stdout or r1.stderr or "")[-140:]))
r2 = subprocess.run([sys.executable, os.path.join(SIM, "Scripts",
                     "ClaimCheck.py")], capture_output=True, text=True,
                    timeout=1200, env=env)
kit2 = json.load(open(os.path.join(SIM, "file_now_kit.json"),
                      encoding="utf-8-sig"))
ok2 = (r2.returncode == 0 and
       bool((kit2.get("claim_audit") or {}).get("ts")))
print("the claim-audit in the sim tree:", "PASS" if ok2 else
      "FAIL: " + (r2.stdout or r2.stderr or "")[-140:])
open(os.path.join(SIM, "the_runner_proof.txt"), "w").write(
    "the runner-portable test passed" if (ok1 and ok2) else "FAIL")
print("RUNNER-PORTABLE:", "PASS <- the outsource works" if (ok1 and ok2)
      else "FAIL")