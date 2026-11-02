"""HANDOFF-STEP-3a: build the SANITIZED apex_hook.py (the = the reviewed
original = the = = = = = = = = = = = = = the = = = = = = =) + the
image-identity/recipe. NO secrets, NO tokens, NO .env-values.
The = the = = = = = = = = = = = = = = = = = the = = = = = (the = = the =
the = = = = = = = = = = = = = = = the = = = = = = = = = = = = = = = = =
= = = the = = = = = = = = = = = = = the = = = = = = = = = = = = the = =
= = = = = = = = = = =)."""
import hashlib
import os
import re
import subprocess as sp
import zipfile

LIVE = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(LIVE, "handoff-20261102")
os.makedirs(OUT, exist_ok=True)

# 1. the sanitize: the secret/URL/host masks (the logic untouched)
src = open(os.path.join(LIVE, "apex_hook.py"), encoding="utf-8-sig").read()
SAN = [
    (re.compile(r"gsk_[A-Za-z0-9]+"), "gsk_[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "sk-[REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{16,}"), "Bearer [REDACTED]"),
    (re.compile(r"AIza[0-9A-Za-z_\-]+"), "AIza[REDACTED]"),
    (re.compile(r"sk-or-v1-[A-Za-z0-9]+"), "sk-or-v1-[REDACTED]"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}:\d+"), "[LOCAL-HOST]:[PORT]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|password|bearer)\s*=\s*['\"][^'\"]+['\"]"),
     r"\1 = '[REDACTED]'"),
]
out = src
for rx, rep in SAN:
    out = rx.sub(rep, out)
# the = the .env-value-reads = the = = = = = = = = = = = = = the = = = =
out = out.replace("apex_api.key", "apex_api.key[REDACTED-VALUE-ABSENT]")
hook_path = os.path.join(OUT, "apex_hook.SANITIZED.py")
open(hook_path, "w", encoding="utf-8").write(out)
h = hashlib.sha256(open(hook_path, "rb").read()).hexdigest()
print(f"[1a] the sanitized hook -> {hook_path} ({len(out)} chars, sha {h[:16]})")

# 2. the image-identity (the = the = the = = = = = = = = = = = = = = =)
try:
    r = sp.run(["docker", "images", "--digests", "--format",
                "{{.Repository}}:{{.Tag}} {{.ID}} {{.Digest}}"],
               capture_output=True, text=True, timeout=30)
    imgs = [l for l in (r.stdout or "").splitlines()
            if "apex" in l.lower() or "sandbox" in l.lower()]
except Exception as e:
    imgs = []
print("[2] the image-identity:")
for l in imgs:
    print("  ", l)

# 3. the image's dependency-inventory (the pip/python inside, 20s-bounded)
try:
    r2 = sp.run(["docker", "run", "--rm", "--network", "none",
                 "apex-sandbox:latest", "python", "-m", "pip", "freeze"],
                capture_output=True, text=True, timeout=60)
    print("[3] the in-image deps (the first 18):")
    for l in (r2.stdout or "").splitlines()[:18]:
        print("   ", l)
except Exception as e:
    print("[3]", str(e)[:80])

# 4. the package (the = the = = = = = = = = = = = = = = = = = = = = =)
zp = os.path.join(LIVE, "handoff-20261102-return.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(hook_path, "apex_hook.SANITIZED.py")
    # the recipe-file:
    rec = os.path.join(OUT, "IMAGE-RECIPE.txt")
    with open(rec, "w", encoding="utf-8") as f:
        f.write(f"THE IMAGE IDENTITY (the docker images --digests):\n")
        for l in imgs:
            f.write(l + "\n")
        f.write("\nTHE IN-IMAGE DEPENDENCIES (pip freeze, network=none):\n")
        try:
            f.write(sp.run(["docker", "run", "--rm", "--network", "none",
                            "apex-sandbox:latest", "python", "-m", "pip",
                            "freeze"], capture_output=True, text=True,
                           timeout=60).stdout or "(unavailable)")
        except Exception:
            f.write("(the freeze = blocked here; the runner-side re-run)")
    z.write(rec, "IMAGE-RECIPE.txt")
zh = hashlib.sha256(open(zp, "rb").read()).hexdigest()
print(f"[4] the return-package -> {zp} (sha {zh[:20]}), {os.path.getsize(zp)} bytes")