import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
# 1. the HONEST ledger row + the brief (the PR's receipt)
with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": "upward",
                        "what": "FIRST-EXTERNAL-PR (founder-granted)",
                        "url": "https://github.com/rtk-ai/rtk/pull/4929"})
            + "\n")
pmf = os.path.join(ROOT, "Config", "PathMemory.json")
pm = json.load(open(pmf, encoding="utf-8-sig"))
h = pm.setdefault("andrew_help", {})
h["briefs"] = int(h.get("briefs", 0)) + 1
h.setdefault("earn_briefs", []).append(
    {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
     "text": "FIRST PR FILED: rtk-ai/rtk#4929 (the muse provider bundle; "
             "disclosed; founder-granted) - awaiting the maintainer's "
             "review"})
from SafeIO import write_json as wj
wj(pmf, pm)
# 2. THE SPEND LAW'S DEFAULT: $0.00 (nothing costs USD without the
# founder's explicit cap; the free-only world until he sets one)
g = json.load(open(os.path.join(ROOT, "Config", "spend_gate.json"),
                   encoding="utf-8-sig"))
g["session_cap_usd"] = 0.0
g["note"] = ("THE FOUNDER'S LAW (2026-11-01): free actions run "
             "automatically; NOTHING that costs USD runs without "
             "Andrew's explicit cap-setting here.")
with open(os.path.join(ROOT, "Config", "spend_gate.json"), "w",
          encoding="utf-8") as f:
    json.dump(g, f, indent=1)
print("the receipts + the $0.00 spend default are in place")