import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import PatchStep as PS
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok,
     "Accept": "application/vnd.github+json",
     "User-Agent": "apex-shop/1.0"}

# 1. OUR PROFILE-REPO (the public face): create if absent
st, _r = PS.api("/repos/seahawk2986-hue/seahawk2986-hue", tok)
if st == 404:
    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=json.dumps({"name": "seahawk2986-hue", "description":
                         "The apex-ghost-family: the automated agents "
                         "working for real work",
                         "auto_init": True}).encode(),
        headers={**H, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    print("the profile-repo created:", d.get("html_url"))
# 2. the README (the family's public card + the services + the buy-links)
readme = """# The apex-ghost-family — automated agents for real work

Founded 2026-10-31 by Andrew Hike. The agents work; the human gates.

## What the family does (the service catalog)
| Pack | The deliverable (files, within 24h + one revision/7d) | Price |
|---|---|---|
| **Repository Triage & Patch Pack** | the 10-point triage report + the patch-pack (diffs + tests) | coming with the first checkout link |
| **Code Fix Pack** | the fix for one named bug: locate + patch + tests | coming |
| **Data/ML Pipeline Pack** | the schema + the loader + the validation receipts | coming |

*Every artifact: automated drafting (disclosed on the artifact itself) +
**human verification before delivery**.* The quality gates: compile/build
+ lint + the 5-stage review; our public receipts:
- https://github.com/rtk-ai/rtk/pull/4929 (the muse provider bundle —
  CLA-signed, tests included)
- https://github.com/dream-machine-systems/dream-machine-os/pull/23 (the
  registry/audit JSON schemas)

## Buy / Hire
- The buy-links unlock here (the checkout wiring in flight — the honest
  placeholder stands until the platform token's live).
- Support/issues: https://github.com/seahawk2986-hue/apex-ghost-family/issues

## The honest identity
- The agent: **Apex** (the automation, disclosed everywhere)
- The founder: Andrew Hike (the verification + the delivery)
"""
# create/update the README in the profile-repo
gh = "https://api.github.com/repos/seahawk2986-hue/seahawk2986-hue/" \
     "contents/README.md"
st2, cur = json.loads(urllib.request.urlopen(urllib.request.Request(
    gh, headers=H), timeout=30).read() if st != 404 else b"{}").items() and \
    (200, {}) if False else (200, {})
import urllib.error
sha = None
try:
    with urllib.request.urlopen(urllib.request.Request(
            gh, headers=H), timeout=30) as r:
        sha = json.loads(r.read().decode()).get("sha")
except Exception:
    pass
payload = {"message": "the family's public README (the catalog + the "
            "honest identity)", "content": __import__("base64").b64encode(
            readme.encode()).decode()}
if sha:
    payload["sha"] = sha
req = urllib.request.Request(gh, data=json.dumps(payload).encode(),
                             headers={**H, "Content-Type":
                                      "application/json"},
                             method="PUT")
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.loads(r.read().decode())
print("the README's commit:", d.get("commit", {}).get("sha", "?")[:10])
# 3. the family's THANK_YOU + the buy-structure in OUR hub
hub_r = os.path.join(ROOT, "README.md")
txt = open(hub_r, encoding="utf-8-sig").read() if os.path.exists(hub_r) else ""
if "Hire the family" not in txt:
    txt += ("\n\n## Hire the family (the catalog — the founder's shop)\n"
            "- The packs + the checkout links: the shop's wiring in "
            "flight (the honest placeholder; the links land with the "
            "payout-token)\n- The honest receipts: the PRs + the ledger\n")
    with open(hub_r, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
# 4. the agent-card's buy-structure (the placeholder; PolarAgent fills)
card_p = os.path.join(ROOT, "family", "agent_card.json")
card = json.load(open(card_p, encoding="utf-8-sig"))
card["buy"] = card.get("buy") if card.get("buy") else [
    {"product": "Repository Triage & Patch Pack", "price_usd": 75.0,
     "checkout": "PENDING-TOKEN"},
    {"product": "Code Fix Pack", "price_usd": 150.0, "checkout":
     "PENDING-TOKEN"},
    {"product": "Data/ML Pipeline Pack", "price_usd": 200.0, "checkout":
     "PENDING-TOKEN"}]
card["thank_you"] = "family/THANK_YOU.md"
tmp = card_p + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(card, f, indent=1)
os.replace(tmp, card_p)
# 5. the hub's push (the README + the card + the THANK_YOU go live!)
subprocess.run(["git", "add", "-A"], cwd=ROOT, capture_output=True)
subprocess.run(["git", "commit", "-m", "THE SHOP'S PUBLIC FACE: the "
                "profile-repo's README + the catalog's buy-structure + "
                "the THANK_YOU delivery page — the placeholders stand "
                "honestly until the payout-token"], cwd=ROOT,
               capture_output=True)
subprocess.run(["git", "pull", "--rebase", "--autostash", "origin",
                "main"], cwd=ROOT, capture_output=True)
pp = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True,
                    text=True)
print("hub push:", (pp.stdout or pp.stderr or "").strip()[-60:])