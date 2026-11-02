"""THE STAGING-INTAKE: backup the live adapter first, then extract the
fixture-package to a STAGING dir (never deploy); print the review-docs."""
import os
import shutil
import zipfile

LIVE = r"C:\Users\seaha\Apex-Adapter"
BACKUP = r"C:\Users\seaha\Apex-Adapter-Backup-pre-fixture-20261102"
STAGE = r"C:\Users\seaha\Apex-Adapter-FixtureStaging"
ZOOP = r"C:\Users\seaha\Downloads\Apex-Repair-FIXTURE-TESTED-20261102.zip"

# 1. THE BACKUP (the source + the settings + the state; NO venv-heavy)
if not os.path.isdir(BACKUP):
    shutil.copytree(
        LIVE, BACKUP,
        ignore=shutil.ignore_patterns("checkpoints", "jobs", "tool_events",
                                      "__pycache__", "*.zip", "ghostnet",
                                      "node_modules"))
    print(f"[backup] the live adapter -> {BACKUP}")
else:
    print("[backup] exists (kept)")

# 2. THE STAGING-EXTRACT
if os.path.isdir(STAGE):
    shutil.rmtree(STAGE)
with zipfile.ZipFile(ZOOP) as z:
    z.extractall(STAGE)
print(f"[staging] extracted -> {STAGE}")

# 3. the review-docs = printed
for rel in ("Apex-Repair-Candidate/README.md",
            "Apex-Repair-Candidate/INSTALL-AND-VERIFY.md"):
    p = os.path.join(STAGE, rel)
    print(f"\n{'=' * 64}\n== {rel}\n{'=' * 64}")
    print(open(p, encoding="utf-8", errors="replace").read()[:2800])