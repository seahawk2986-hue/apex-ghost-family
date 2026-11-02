"""THE UNFLIP: byte-restore the LIVE engine from the PRE-FLIP copy,
hash-prove it = back to the known-good, restart the adapter."""
import hashlib
import os
import shutil

LIVE = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
ORIG_KEEP = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
             r"\staged-candidate\v2_job_engine.PRE-FLIP.py")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

before = sha(LIVE)
shutil.copy2(ORIG_KEEP, LIVE)
after = sha(LIVE)
print("[unflip]: live", before[:16], "-> restored", after[:16])
assert sha(LIVE) == sha(ORIG_KEEP), "restore mismatch - refusing to continue"
print("[VERDICT]: live engine = byte-identical to the pre-flip original")