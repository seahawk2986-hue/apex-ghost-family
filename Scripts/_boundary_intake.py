"""THE BOUNDARY INTAKE: (1) all 13 staged-file hashes vs the MANIFEST;
(2) the LIVE companion vs the STAGED companion = an exact unified diff so
any 'newer unrelated live change' = visible before anything is applied."""
import difflib
import hashlib
import json
import os

ROOT = r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102\Apex-V1-Chat-Boundary"
LIVE = r"C:\Users\seaha\Apex-Adapter"

man = json.load(open(os.path.join(ROOT, "MANIFEST.json"),
                     encoding="utf-8-sig"))
ok = bad = 0
for f in man["files"]:
    p = os.path.join(ROOT, f["path"])
    if not os.path.exists(p):
        print(f"  MISSING {f['path']}")
        bad += 1
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if h == f["sha256"]:
        ok += 1
    else:
        print(f"  MISMATCH {f['path']}: staged {h[:12]} != manifest {f['sha256'][:12]}")
        bad += 1
print(f"[staged-hash verify]: {ok}/{ok + bad} match MANIFEST"
      f" ({bad} problems)")

# (2) the live-vs-staged companion diff
lp = os.path.join(LIVE, "companion.py")
sp = os.path.join(ROOT, "source", "companion.py")
live = open(lp, encoding="utf-8-sig", errors="replace").readlines()
staged = open(sp, encoding="utf-8-sig", errors="replace").readlines()
print(f"[companion] live={os.path.getsize(lp)}b staged="
      f"{os.path.getsize(sp)}b  identical={live == staged}")
diff = list(difflib.unified_diff(live, staged, "live", "staged", n=2))
print(f"[diff hunks]: {len(diff)} lines total")
show = diff if len(diff) <= 80 else diff[:40] + ["  ..."] + diff[-40:]
for d in show:
    print("   ", d.rstrip()[:150])
if live == staged:
    print("[VERDICT]: staged companion = byte-identical to live (safe apply)")
else:
    print("[VERDICT]: STAGED COMPANION DIFFERS from live - apply SURGICALLY,"
          " never as a full-baseline overwrite")