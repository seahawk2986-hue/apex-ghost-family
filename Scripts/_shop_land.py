import json
import os
import subprocess
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": "upward",
                        "what": "SHOP-LIVE-WIRED: the 3 buy-links in the "
                                "card/catalog/doors/README"})
            + "\n")
subprocess.run(["git", "add", "-A"], cwd=ROOT, capture_output=True)
subprocess.run(["git", "commit", "-m",
                "SHOP-LIVE WIRING COMPLETE: the 3 buy.polar.sh links in "
                "the agent-card + the catalog + the doors + the hub "
                "README - the buy-side live; the shop's honest receipts "], cwd=ROOT,
               capture_output=True)
subprocess.run(["git", "pull", "--rebase", "--autostash", "origin",
                "main"], cwd=ROOT, capture_output=True)
pp = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True,
                    text=True, timeout=120)
print("push:", (pp.stdout or pp.stderr or "").strip()[-60:])