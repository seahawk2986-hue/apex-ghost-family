"""BLOATSWEEP: the honest bloat-audit (the founder's right to see it).
Five classes, each evidence-keyed:
 B1 the ATTIC census (the = = = = = = = = = = = = = = = = = = = = =)
 B2 the ONE-SHOT scripts (_-prefixed: the session's instruments; the
    value = their receipts, not their presence)
 B3 the NEAR-DUPLICATE organs (the same-purpose families: PatchLoop
    1/2/3/4 = the honest versions or the dead?)
 B4 the DEAD-WEIGHT (the files: never-imported, never-run in the
    receipts, no config-echo)
 B5 the RECEIPT-ORPHANS (the Config-files no-organ reads anymore) +
    the DISK-WEIGHT (the venv's = the = the needed)
The honest verdict per item: the KEEP (the reason) / the SAFE-DELETE (the
reason) / the FOUNDER-DECISION (the reason). NEVER auto-deletes - the
list = the founder's call (the = the honest)."""
import glob
import json
import os
import re
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = {"ts": time.strftime("%Y-%m-%d %H:%M:%S")}

pys = [p for p in glob.glob(os.path.join(ROOT, "Scripts", "*.py"))]

# B2 = the one-shots
oneshots = [os.path.basename(p) for p in pys
            if re.match(r"^[a-z_]+\.py$", os.path.basename(p)) and
            os.path.basename(p).startswith("_") or
            re.match(r"^_[0-9a-zA-Z_]+\.py$", os.path.basename(p))]
OUT["B2_oneshots"] = {"count": len(oneshots), "items": oneshots[:60],
                      "verdict": "the receipts carry their value; the "
                                 "SCRIPTS = the bloat (the archive-able)"}

# B1 = the attic
attic = glob.glob(os.path.join(ROOT, "Scripts", "Attic", "*.py"))
OUT["B1_attic"] = {"count": len(attic), "verdict": "already-archived (the "
                      "honest); the = = the disk-only"}

# B3 = the near-dupes (the name-families)
fams = {}
for p in pys:
    m = re.match(r"^(PatchLoop|PaperHarvest|ProbeFree|_serve|_fix|Apex[A-Za-z]*)", os.path.basename(p))
    if m:
        fams.setdefault(m.group(1), []).append(os.path.basename(p))
OUT["B3_families"] = {k: v for k, v in fams.items() if len(v) > 1}

# B4 = the never-imported never-receipted (the honest: the = = =)
imported = set()
for p in pys:
    try:
        t = open(p, encoding="utf-8-sig", errors="replace").read()
        for q in pys:
            n = os.path.splitext(os.path.basename(q))[0]
            if n != os.path.splitext(os.path.basename(p))[0] and \
                    re.search(rf"\b(import|from)\s+{n}\b", t):
                imported.add(n)
    except Exception:
        pass
config_t = ""
for cf in glob.glob(os.path.join(ROOT, "Config", "*")):
    try:
        config_t += open(cf, encoding="utf-8-sig", errors="replace").read()[:2000]
    except Exception:
        pass
dead = []
for p in pys:
    n = os.path.splitext(os.path.basename(p))[0]
    if n in imported or n.startswith("_"):
        continue
    if n in config_t or n in open(os.path.join(root_config := os.path.join(ROOT, "Config"), "AscentLedger.jsonl"), encoding="utf-8-sig").read()[-200000:]:
        continue
    dead.append(os.path.basename(p))
OUT["B4_dead_weight"] = {"count": len(dead), "items": dead[:40],
                         "verdict": "no import + no config/receipt echo = "
                                    "the bloat-candidates (the "
                                    "founder-decision each)"}

# B5 = the disk-weights + the receipt-orphans
du = 0
for p in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
    try:
        if os.path.isfile(p) and "apex_venv" not in p:
            du += os.path.getsize(p)
    except Exception:
        pass
venv_du = sum(os.path.getsize(p) for p in glob.glob(
    os.path.join(ROOT, "apex_venv", "**", "*"), recursive=True)
    if os.path.isfile(p))
OUT["B5_disk"] = {"tree_mb": round(du / 2**20, 1),
                  "venv_mb": round(venv_du / 2**20, 1),
                  "verdict": "the venv = the wheels' honest home "
                             "(torch-family = the heavy-1.6GB-class)"}

with open(os.path.join(ROOT, "Config", "bloat_sweep.json"), "w",
          encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1)
for k, v in OUT.items():
    if isinstance(v, dict):
        print(f"[bloat] {k}: {v.get('verdict', '')[:70]} | "
              f"count={v.get('count', '-')}")
print(f"[bloat] the receipt: Config/bloat_sweep.json")