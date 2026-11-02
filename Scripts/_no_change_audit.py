"""THE NO-CHANGE AUDIT: did the boundary-round change ANY of Apex?
(1) every .py/.ps1/.pyw in the live ADAPTER vs the pre-boundary backup;
(2) the jobs_registry.json = the post-surgery shape (the _slot = None, the
    91+ job-records intact - the surgery = the leak-clear only);
(3) the SHIPPED Micah-Recon.zip = re-opened + re-hashed vs its own receipt.
The verdict: untouched / any-diff-listed-honestly."""
import hashlib
import json
import os
import time
import zipfile

ADV = r"C:\Users\seaha\Apex-Adapter"
BAK = r"C:\Users\seaha\Apex-Adapter-Backup-pre-boundary-20261102"
ZP = r"C:\Users\seaha\OneDrive\Desktop\Micah-Recon.zip"
DECL = "d514f63a10f5fece7294884d3013bf408a93056a52323aca62167bd18312051d"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

# (1) the adapter's CODE-files (the .py/.ps1/.pyw): the backup-compare
diff, same, missing_in_bak = [], 0, []
for base, _, files in os.walk(ADV):
    if any(x in base for x in (".git", "__pycache__", ".ruff_cache")):
        continue
    for fn in files:
        if not fn.endswith((".py", ".ps1", ".pyw")):
            continue
        p = os.path.join(base, fn)
        rel = os.path.relpath(p, ADV)
        bp = os.path.join(BAK, rel)
        if not os.path.exists(bp):
            missing_in_bak.append(rel)
            continue
        if sha(p) == sha(bp):
            same += 1
        else:
            diff.append(rel)
print("== the adapter's CODE (vs the pre-boundary backup) ==")
print(f"[byte-identical]: {same} files | [DIFFER]: {len(diff)} | "
      f"[new-since-backup]: {len(missing_in_bak)}")
for d in diff:
    print("   DIFF:", d)
for m in missing_in_bak[:10]:
    print("   NEW:", m)

# (2) the registry's post-surgery truth
if os.path.exists(os.path.join(ADV, "jobs_registry.json")):
    reg = json.load(open(os.path.join(ADV, "jobs_registry.json"),
                         encoding="utf-8-sig"))
    print("\n== the jobs_registry ==")
    print("[_slot]:", reg.get("_slot"), "| [jobs rows]:",
          len(reg.get("jobs", {})), "| [checkpoints]:",
          len(reg.get("checkpoints", {})))

# (3) the shipped zip = the re-verify vs its declared sha
zsha = sha(ZP)
print("\n== the Micah-Recon.zip ==")
print("[zip sha256]:", zsha[:32], "...", "| [matches the declaration]:",
      zsha == DECL)
with zipfile.ZipFile(ZP) as z:
    for name in z.namelist():
        if name.endswith((".py",)):
            data = z.read(name)
            print(f"  {name.split('/')[-1]}: "
                  f"sha={hashlib.sha256(data).hexdigest()[:16]} "
                  f"({len(data):,}b)")
    rj = json.loads(z.read("Micah-Recon/receipt.json"))
    print("  [receipt keys intact]:", sorted(rj["files"].keys()))

print("\n[ts]:", time.strftime("%Y-%m-%d %H:%M:%S"))