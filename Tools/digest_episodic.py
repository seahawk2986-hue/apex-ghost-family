"""digest_episodic - the OFF-BOX organ (Actions runner): digests the GI-gym
feed into progress receipts. Pure-text; no keys; no model calls; $0."""
import collections
import json
import pathlib

R = pathlib.Path(__file__).resolve().parents[1]
S = R / "scores"
S.mkdir(exist_ok=True)
rows = []
p = R / "memory_episodic.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
cal = [r for r in rows if r.get("kind") == "calibration" and "gym" in r.get("text", "")]
lessons = [r for r in rows if r.get("kind") == "lesson"][-10:]
hits = sum(1 for r in cal if "HIT" in r.get("text", ""))
misses = sum(1 for r in cal if "MISS" in r.get("text", ""))
by_fam = collections.Counter()
for r_ in cal:
    for f in ("arithmetic-chain", "math-word", "predict-output", "spot-the-flaw"):
        if f in r_.get("text", ""):
            by_fam[f] += 1
            break
lines = ["# The GI-gym progress (distilled off-box; the runner organ)", "",
         f"drills: {len(cal)} (HIT {hits} / MISS {misses}"
         + (f" = {hits / max(1, hits + misses) * 100:.0f}% hit-rate)" if cal else ")"),
         "families (drills):", *[f"- {k}: {v}" for k, v in by_fam.items()],
         "", "## the newest durable lessons"]
lines += [f"- {r.get('text','')}" for r_ in [r for r in rows if r.get('kind') == 'lesson'][-8:]]
(S / "gi_progress.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"[distilled off-box]: drills={len(cal)} HIT={hits} MISS={misses} "
      f"-> scores/gi_progress.md")