"""THE SWARM's SPREAD-REPORT: veins, repos-touched, the lead-queues, the
findings-by-source, the pushed grain-commits (= the spread onto GitHub)."""
import json
import collections

ADV = r"C:\Users\seaha\Apex-Adapter"

def load(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return default

s = load(ADV + r"\swarm_state.json", {})
s1 = load(ADV + r"\swarm_state_shard1.json", {})
s2 = load(ADV + r"\swarm_state_shard2.json", {})
print("== the state ==")
print("[main]:", {k: (str(v)[:70]) for k, v in list(s.items())[:14]})
for name, sh in (("shard1", s1), ("shard2", s2)):
    if sh:
        print(f"[{name}]:", {k: (str(v)[:60]) for k, v in list(sh.items())[:8]})

# the findings: the src-mix + the tiers + the unique-repos
src, tiers, repos = collections.Counter(), collections.Counter(), set()
n = 0
try:
    for line in open(ADV + r"\swarm_findings.jsonl", encoding="utf-8-sig",
                     errors="ignore"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        n += 1
        src[r.get("src")] += 1
        tiers[r.get("tier")] += 1
        repo = str(r.get("repo") or "")
        if "/" in repo:
            repos.add(repo)
except Exception as e:
    print("[findings read]", str(e)[:80])
print("\n== the spread ==")
print(f"[findings]: {n} | [unique repos touched]: {len(repos)}")
print(f"[by source]: {dict(src)}")
print(f"[by tier]: {dict(tiers)}")
print("[pending leads queued]:", len(s.get("pending_leads") or []) +
      len(s1.get("pending_leads") or []) + len(s2.get("pending_leads") or []))

# the pushed grain (the spread = ON GitHub: the hub-harvest commits)
import subprocess as sp
out = sp.run(["git", "log", "--oneline", "--all", "--grep", "hub harvest"],
             cwd=r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
             capture_output=True, text=True, timeout=60)
grains = [l for l in (out.stdout or "").splitlines() if l.strip()]
print(f"[grain-commits pushed to GitHub]: {len(grains)}")
print("[latest]:", grains[-1][:100] if grains else "(none)")