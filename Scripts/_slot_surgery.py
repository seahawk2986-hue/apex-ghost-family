"""THE SLOT-SURGERY (receipted): the crash-leaked _slot = removed from the
PERSISTED registry (the adapter must be stopped while this edits it)."""
import json
import os

P = r"C:\Users\seaha\Apex-Adapter\jobs_registry.json"
data = json.load(open(P, encoding="utf-8-sig"))
slot = data.get("_slot")
print("[stale slot-holder]:", slot)
if slot:
    rec = data.get("jobs", {}).get(slot, {})
    print("  its state:", rec.get("state"), "| worker-known-dead:",
          rec.get("processes_stopped"))
    data.pop("_slot", None)
    tmp = P + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, P)
    print("[surgery]: _slot cleared + registry atomically flushed")
else:
    print("[surgery]: slot already free - nothing to do")
print("[post]: _slot =", json.load(open(P, encoding="utf-8-sig")).get("_slot"))