"""THE VET-LINE (the swarm's ROI-promoter): turn the scouts' 21K scored
findings into VETTED LIBRARY SKILLS. Feed = the leads (src=lead, tiers
GOLD/VEIN, scored) -> dedupe-vs-already-harvested -> top-N repos ->
the Library's OWN harvest(repo, per_source) = fetch->compile->bandit->
import-allowlist->register(sha+provenance). Bounded: N repos, one file/
lead-class, the RAM-gate 2.2GB, wall-capped; $0 (the GitHub free-API)."""
import json
import os
import sys
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADV = r"C:\Users\seaha\Apex-Adapter"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))

RAM = psutil.virtual_memory()
ok_ram = RAM.available / 2 ** 30 >= 2.2
print(f"[RAM-gate]: {RAM.available / 2**30:.2f}GB free (need 2.2):",
      "GO" if ok_ram else "HOLD (the canon law stops the heavy organ)")
if not ok_ram:
    raise SystemExit(0)

# THE SINGLE-FLIGHT LOCK: two fires never race one library-write
import msvcrt
_lockf = open(os.path.join(ROOT, "Logs", "vetline.flight"), "a")
try:
    msvcrt.locking(_lockf.fileno(), msvcrt.LK_NBLCK, 1)
except Exception:
    raise SystemExit(0)  # an instance = already running: the honest no-op

import SkillLibrary as SL  # noqa: E402  (the after-gate import)

log = os.path.join(ROOT, "Logs", "vetline.log")
def vlog(m):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + m
    try:
        open(log, "a", encoding="ascii", errors="replace").write(line + "\n")
    except Exception:
        pass
    print("  ", line[:130], flush=True)

T0 = time.time()
WALL = 330  # the bounded run: ~5.5 minutes max, then the honest stop

# 1. the feed: the scored leads (never the local self-scans)
fl = os.path.join(ADV, "swarm_findings.jsonl")
leads = {}
for line in open(fl, encoding="utf-8-sig", errors="ignore"):
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get("src") != "lead":
        continue
    repo = str(r.get("repo") or "").strip()
    if not repo or "/" not in repo:
        continue
    score = float(r.get("score") or 0)
    cur = leads.get(repo)
    if cur is None or score > cur[0]:
        leads[repo] = (score, r.get("tier"),
                       r.get("stars") or 0, r.get("license_source"))
leads = [(v[0], k, v[1], v[2], v[3]) for k, v in leads.items()]

# 2. skip everything the library already harvested
lib = SL.load()
have = {s.get("source_repo") for s in lib.get("skills", [])}
fresh = [x for x in leads if x[1] not in have]
fresh.sort(key=lambda x: -x[0])
per_source = 6
top = fresh[:18]
vlog(f"[feed]: {len(leads)} scored leads | fresh-repos: {len(fresh)} "
     f"| target top-{len(top)} x {per_source}/repo")
before_n = len(lib.get("skills", []))

# 3. the promotion: the Library's OWN vet+register discipline per repo
did = 0
for score, repo, tier, stars, lic in top:
    if time.time() - T0 > WALL:
        vlog("[wall]: the honest stop (bounded run ends)")
        break
    try:
        got = SL.harvest(repo, per_source=per_source)
        did += 1
        vlog(f"[harvest] {repo} (score {score}, {tier}): "
             f"{json.dumps(got, default=str)[:90]}")
    except Exception as e:
        vlog(f"[harvest FAIL] {repo}: {str(e)[:80]}")

lib2 = SL.load()
after_n = len(lib2.get("skills", []))
vlogged_new = after_n - before_n
vlog(f"[DELTA]: skills {before_n} -> {after_n} (+{vlogged_new}, vetted)")
vlog(f"[run wall]: {round(time.time() - T0, 1)}s | repos tried: {did}")