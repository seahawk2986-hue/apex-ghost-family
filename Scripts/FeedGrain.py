"""FeedGrain - the LOCAL side of the A+ conversion: every 15 min
(a) write family/leads_grain.json = the TOP scored fresh leads, ordered,
    minus what the library already harvested,
(b) git pull --rebase (the runner's vetted-library lands), sync the ledger,
(c) commit + push the feed. Zero secrets, [skip ci], $0."""
import json
import os
import subprocess as sp
import sys

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADV = r"C:\Users\seaha\Apex-Adapter"
GRAIN = os.path.join(ROOT, "family", "leads_grain.json")
LIB = os.path.join(ROOT, "Config", "SkillLibrary.json")

os.chdir(ROOT)
sp.run(["git", "pull", "--rebase"], capture_output=True, text=True, timeout=120)
try:
    sp.run(["git", "push"], capture_output=True, text=True, timeout=120)
except Exception:
    pass

lib = json.load(open(LIB, encoding="utf-8-sig"))
have = {s.get("source_repo") for s in lib.get("skills", [])}
leads = {}
for line in open(os.path.join(ADV, "swarm_findings.jsonl"),
                 encoding="utf-8-sig", errors="ignore"):
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get("src") != "lead":
        continue
    repo = str(r.get("repo") or "").strip()
    if repo in have or "/" not in repo:
        continue
    sc = float(r.get("score") or 0)
    if repo not in leads or sc > leads[repo]["score"]:
        leads[repo] = {"repo": repo, "score": sc, "tier": r.get("tier"),
                       "stars": r.get("stars") or 0,
                       "license": r.get("license_source") or ""}
ordered = sorted(leads.values(), key=lambda x: -x["score"])[:2500]

# THE CHURN GATE (2026-11-04, repo-hygiene repair): only rewrite + commit
# when the LEAD SET actually changed; the ts field alone never counts as a
# change. This ends the hourly "leads: the vet-feed 514" append-log spam
# that grew .git into a journal of identical grains. Bug named where born:
# Scripts/FeedGrain.py lines 42-48 (the version before this comment).
prev = {}
if os.path.exists(GRAIN):
    try:
        prev = json.load(open(GRAIN, encoding="utf-8-sig"))
    except Exception:
        prev = {}
if prev.get("leads") == ordered:          # same leads = same grain = no-op
    print(f"[feed]: {len(ordered)} ordered leads UNCHANGED (no write, no "
          f"commit - the honest quiet round)")
    sys.exit(0)
tmp = GRAIN + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
               "count": len(ordered), "leads": ordered}, f, indent=1)
os.replace(tmp, GRAIN)
print(f"[feed]: {len(ordered)} ordered leads written (lead-set changed)")

r = sp.run(["git", "add", "family/leads_grain.json"], capture_output=True,
           text=True, timeout=60)
d = sp.run(["git", "diff", "--cached", "--quiet"], capture_output=True,
           timeout=60)
if d.returncode != 0:
    c = sp.run(["git", "commit", "-m", "leads: the vet-feed "
                + str(len(ordered)) + " (scored-ordered) [skip ci]"],
               capture_output=True, text=True, timeout=120)
    p = sp.run(["git", "pull", "--rebase"], capture_output=True, text=True,
               timeout=120)
    pp = sp.run(["git", "push"], capture_output=True, text=True, timeout=120)
    print("[grain pushed] commit:", (c.stdout or "").strip()[:80],
          "| push:", (pp.stdout or "").strip().splitlines()[-1][:60]
          if (pp.stdout or "").strip() else "refused (honest retry next fire)")