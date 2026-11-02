"""Register web-harvest in the actions-ladder + one local verify-run."""
import json

p = "Config/apex10_actions.json"
d = json.load(open(p, encoding="utf-8-sig"))
# the file = a dict wrapper: find the list-valued key (the actions)
if isinstance(d, list):
    wrap = None
    items = d
else:
    wrap = d
    items = next((v for v in d.values() if isinstance(v, list)), None)
    if items is None:
        raise SystemExit("the actions-list = not found in the wrapper")
if not any(isinstance(a, dict) and a.get("id") == "web-harvest" for a in items):
    items.append({"id": "web-harvest", "script": "WebHarvest.py",
                  "runner": "actions", "ram_needed": 0.0,
                  "capability": "omnivore",
                  "why": "the 44-canon-URLs' fetch+extract = ON THE RUNNERS "
                         "(the founder's outsourcing-order); rows = receipts",
                  "done": False})
    if wrap is not None:
        key = next(k for k, v in d.items() if v is items)
        d[key] = items
        json.dump(d, open(p, "w", encoding="utf-8"), indent=1)
    else:
        json.dump(items, open(p, "w", encoding="utf-8"), indent=1)
print("[actions-registered]: web-harvest (runner=actions)")

import sys
sys.path.insert(0, "Scripts")
import WebHarvest
ok, tot = WebHarvest.main()
print(f"[local-verify run]: {ok}/{tot}")