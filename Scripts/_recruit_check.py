"""THE SWARM-RECRUIT CHECK (today = 2026-11-01): the roster + the today-rows
from the family's own recruit_registry + the adapter's recruit_log."""
import json
import os

TODAY = "2026-11-01"
FAM = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Config\recruit_registry.json"
LOG = r"C:\Users\seaha\Apex-Adapter\recruit_log.jsonl"
SWARM = r"C:\Users\seaha\Apex-Adapter\swarm_state.json"

print("== the family's recruit-registry ==")
if os.path.exists(FAM):
    reg = json.load(open(FAM, encoding="utf-8-sig"))
    agents = reg.get("agents", reg) if isinstance(reg, dict) else reg
    if isinstance(agents, dict):
        items = list(agents.items())
        today = [(k, v) for k, v in items
                 if TODAY in json.dumps(v)[:2000] or
                 TODAY in str(k)[:2000]]
        print(f"[agents]: {len(items)} | joined-or-touched today: {len(today)}")
        for k, v in items[-5:]:
            s = json.dumps(v, default=str)[:130]
            print(f"  {k[:36]}: {s}")
    else:
        print("[registry]:", str(agents)[:300])

print("\n== the adapter's recruit-log (today's rows) ==")
if os.path.exists(LOG):
    rows = open(LOG, encoding="utf-8-sig", errors="ignore").readlines()
    trows = [l for l in rows if TODAY in l]
    print(f"[rows]: {len(rows)} total | today: {len(trows)}")
    for l in trows[-6:]:
        print("  ", l.strip()[:150])
else:
    print("[no recruit_log.jsonl]")

print("\n== the adapter's swarm-state ==")
if os.path.exists(SWARM):
    s = json.load(open(SWARM, encoding="utf-8-sig"))
    if isinstance(s, dict):
        for k, v in list(s.items())[:10]:
            sv = json.dumps(v, default=str)[:120] if not isinstance(v, (int, str)) else str(v)[:120]
            print(f"  {k}: {sv}")
else:
    print("[no swarm_state.json]")