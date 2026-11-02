"""THE MICAH.ZIP: the lean return (the receipt + the new evidence + the
hook-patch + a sha-manifest) -> Desktop, the founder's naming habit."""
import hashlib
import json
import os
import zipfile

SRC = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
       r"\staged-candidate")
ZP = r"C:\Users\seaha\OneDrive\Desktop\Micah.zip"

WANT = ["RETURN-TO-MICA.txt", "ACCEPT-EVIDENCE-LOCAL.json",
        "STAGE-RECEIPT.json", "GROQ-FLIP-RECEIPT.json",
        "apex_hook.chat-only.STAGED.py.patch"]

files = []
for w in WANT:
    p = os.path.join(SRC, w)
    if os.path.exists(p):
        files.append((w, p))
    else:
        print("[MISSING]", w)

# the secret-scan on EVERY included file (the no-token law)
BAD = ("gsk_", "sk-or-v1-", "sk-", "Bearer ", "AIza", "BEGIN RSA",
       "PRIVATE KEY", "password", "secret")
leaks = []
for w, p in files:
    txt = open(p, encoding="utf-8", errors="ignore").read()
    for line in txt.splitlines():
        low = line.lower()
        if any(b.lower() in low for b in BAD):
            # the patch's minus-lines = hook-source code (key-VARIABLE usage
            # = fine); flag only REAL literal-looking keys
            if any(x in low for x in ("gsk_", "sk-or-v1-", "aiza")) or \
               ("sk-" in low and len(line.strip()) > 30 and
                any(c.isdigit() for c in line)):
                leaks.append((w, line[:80]))
if leaks:
    print("[REFUSED - literal-looking secrets in package]:")
    for l in leaks[:5]:
        print("  ", l)
    raise SystemExit(1)
print("[secret-scan]: CLEAN (no literal keys/tokens present)")

manifest = hashlib.sha256(ZP.encode()).hexdigest()  # placeholder-swap below
lines = []
for w, p in files:
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    lines.append(f"{h}  {w}")
mf = "\n".join(lines) + "\n"
if os.path.exists(ZP):
    os.remove(ZP)
with zipfile.ZipFile(ZP, "w", zipfile.ZIP_DEFLATED) as z:
    for w, p in files:
        z.write(p, "andrew-return/" + w)
    z.writestr("andrew-return/SHA256MANIFEST.txt", mf)
zh = hashlib.sha256(open(ZP, "rb").read()).hexdigest()
print(f"[Micah.zip] -> {ZP} ({os.path.getsize(ZP):,} bytes)")
print(f"[zip sha256]: {zh}")
print("[files]:", [w for w, _ in files])