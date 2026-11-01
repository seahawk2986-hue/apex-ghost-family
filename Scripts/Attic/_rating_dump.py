"""THE RATING-DUMPER: the receipts' honest read for the capability-scorecard."""
import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"


def load(fn):
    p = os.path.join(ROOT, "Config", fn)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception as e:
        return {"_err": str(e)[:60]}


m = load("ApexUpwardManifest.json")
st = m.get("state", {}) if m else {}
g = st.get("goals", st.get("goals_projection", {}))
print(f"[manifest] ts={m.get('ts')} genes: gen {st.get('genes', {}).get('gen')} "
      f"champion={st.get('genes', {}).get('champion')} "
      f"fitness={st.get('genes', {}).get('lineages', {}).get('base', {}).get('fitness')}")
print(f"[manifest] goals tracked: {len(g)}")
for k, v in list(g.items())[:14]:
    if isinstance(v, dict):
        vs = {kk: vv for kk, vv in v.items() if not isinstance(vv, (list, dict))}

        print(f"  {k}: {json.dumps(vs, ensure_ascii=False)[:150]}")

for fn, keys in [
    ("rescan_master.json", None),
    ("reward_audit.json", None),
    ("goal_coherence.json", ("tiers", "clashes", "tensions", "synergies")),
    ("sanitizer_audit.json", None),
    ("skill_gaps.json", None),
    ("benchmark_card.json", ("our_measured",)),
]:
    d = load(fn)
    if d is None:
        print(f"[{fn}] absent")
        continue
    if keys:
        d = {k: d.get(k) for k in keys if k in d}
    print(f"[{fn}] " + json.dumps(d, ensure_ascii=False)[:500])