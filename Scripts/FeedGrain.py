"""FeedGrain - the LOCAL side of the A+ conversion: every 15 min
(a) write family/leads_grain.json = the TOP scored fresh leads, ordered,
    minus what the library already harvested,
(b) git pull --rebase (the runner's vetted-library lands), sync the ledger,
(c) commit + push the feed - ONLY WHEN THE FEED'S CONTENT ACTUALLY CHANGED.

THE 2026-11-04 ANTI-NOISE LAW (the measured bug): the old version wrote a
second-resolution `ts` into the committed JSON on EVERY fire, so the
git-diff gate always saw "a change" -> ~96 no-op commits/day (~8MB/day of
churn; "728" committed 14x IDENTICAL) - every commit-subject lied about
progress. Now: a sha256 CONTENT gate (ts excluded) = a commit only when
real leads changed; an unchanged feed prints its honest no-op and exits.
The existing git-diff gate stays as the belt. Zero secrets, [skip ci], $0."""
import hashlib
import json
import os
import subprocess as sp
import sys
import time

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
payload = {"count": len(ordered), "leads": ordered}
feed_hash = hashlib.sha256(
    json.dumps(payload, sort_keys=True, ensure_ascii=False)
    .encode("utf-8")).hexdigest()

old = {}
try:
    old = json.load(open(GRAIN, encoding="utf-8-sig"))
except Exception:
    pass
if old.get("leads_sha256") == feed_hash:
    print(f"[feed]: {len(ordered)} ordered leads, content UNCHANGED - no "
          "write, no commit (the honest no-op; the ~96-commit/day noise "
          "class is dead)")
    sys.exit(0)

payload["leads_sha256"] = feed_hash
payload["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
tmp = GRAIN + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=1)
os.replace(tmp, GRAIN)
print(f"[feed]: {len(ordered)} ordered leads written (content changed -> commit)")

r = sp.run(["git", "add", "family/leads_grain.json"], capture_output=True,
           text=True, timeout=60)
d = sp.run(["git", "diff", "--cached", "--quiet"], capture_output=True,
           timeout=60)
if d.returncode != 0:
    c = sp.run(["git", "commit", "-m", "leads: the vet-feed "
                + str(len(ordered)) + " (scored-ordered, content-changed) "
                "[skip ci]"],
               capture_output=True, text=True, timeout=120)
    p = sp.run(["git", "pull", "--rebase"], capture_output=True, text=True,
               timeout=120)
    pp = sp.run(["git", "push"], capture_output=True, text=True, timeout=120)
    print("[grain pushed] commit:", (c.stdout or "").strip()[:80],
          "| push:", (pp.stdout or "").strip().splitlines()[-1][:60]
          if (pp.stdout or "").strip() else "refused (honest retry next fire)")
else:
    print("[feed]: the git gate caught a no-op - nothing committed")