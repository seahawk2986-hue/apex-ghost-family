"""THE INTAKE: find the fixture-package, verify its SHA256, list contents."""
import hashlib
import os
import zipfile

CANDIDATES = [
    r"C:\Users\seaha\Downloads\Apex-Repair-FIXTURE-TESTED-20261102.zip",
    r"C:\Users\seaha\Downloads\Apex-Repair-FIXTURE-TESTED-20261102 (1).zip",
    r"C:\Users\seaha\Downloads\Apex-Repair-FIXTURE-TESTED-20261102 (2).zip",
    r"C:\Users\seaha\OneDrive\Desktop\Apex-Repair-FIXTURE-TESTED-20261102.zip",
    r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Apex-Repair-FIXTURE-TESTED-20261102.zip",
    r"C:\Users\seaha\Apex-Adapter\Apex-Repair-FIXTURE-TESTED-20261102.zip",
]
EXPECT = "222c4c72fcf234aae3c639734bbffd869"
found = None
for c in CANDIDATES:
    if os.path.exists(c):
        h = hashlib.sha256(open(c, "rb").read()).hexdigest()
        ok = h.startswith(EXPECT)
        print(f"[found] {c}\n  sha256={h[:20]} {'MATCH' if ok else 'MISMATCH!'}")
        if ok:
            found = c
            break
if not found:
    # a wide sweep (the = the = the = = = = = = = = = = = = = = = = = =)
    for base in (r"C:\Users\seaha\Downloads",
                 r"C:\Users\seaha\OneDrive\Desktop"):
        if not os.path.isdir(base):
            continue
        for fn in os.listdir(base):
            if "FIXTURE" in fn and fn.endswith(".zip"):
                p = os.path.join(base, fn)
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()
                print(f"[sweep] {p} sha={h[:20]} "
                      f"{'MATCH' if h.startswith(EXPECT) else 'mismatch'}")

if found:
    with zipfile.ZipFile(found) as z:
        names = z.namelist()
        print(f"\n[{len(names)} content-files]:")
        for n in sorted(names)[:40]:
            print("  ", n)
else:
    print("\n[the package = NOT FOUND on disk — the handoff text = received, "
          "the zip itself = not-yet-downloaded — tell me its location]")