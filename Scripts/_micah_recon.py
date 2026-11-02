"""THE MICAH RECON-PACKAGE: the CURRENT live companion.py + v2_job_engine.py
(= the acceptance-run's actual engine state; the flip = already reverted,
receipted in the prior Micah.zip) sanitized: secrets removed, home-paths
neutraled, LOGIC INTACT. Hash-receipted; a literal-key = ABORTS the build."""
import hashlib
import json
import os
import re
import time
import zipfile

ADV = r"C:\Users\seaha\Apex-Adapter"
DESK = r"C:\Users\seaha\OneDrive\Desktop"
ZP = os.path.join(DESK, "Micah-Recon.zip")
FILES = ["companion.py", "v2_job_engine.py"]

HOME = "C:\\Users\\seaha"
HOME_NEUTRAL = "C:\\Users\\OWNER"
KEY_RX = re.compile(
    r"gsk_[A-Za-z0-9]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{30,}"
    r"|AIza[0-9A-Za-z_\-]{20,}|AQ\.[A-Za-z0-9_\-]{20,}|Bearer [A-Za-z0-9_\-]{20,}")

receipt = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "files": {}}
payload = {}
for fn in FILES:
    p = os.path.join(ADV, fn)
    raw = open(p, "rb").read()
    orig_sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    hits = HOME.count("\\") and text.count(HOME + "\\")
    n_home = len(re.findall(re.escape(HOME.rstrip("\\")), text))
    key_hits = KEY_RX.findall(text)
    assert not key_hits, f"{fn}: literal-looking KEY present - refuse to ship"
    text = text.replace(HOME + "\\", HOME_NEUTRAL + "\\")
    text = text.replace(HOME, HOME_NEUTRAL)
    assert not (HOME in text and HOME_NEUTRAL not in text), fn + ": home-rem = incomplete"
    assert KEY_RX.search(text) is None, fn + ": post-sanitize key-scan FAILED"
    payload[fn] = text.encode("utf-8")
    receipt["files"][fn] = {"sha256_original": orig_sha,
                            "sha256_sanitized": hashlib.sha256(payload[fn]).hexdigest(),
                            "bytes_original": len(raw),
                            "bytes_sanitized": len(payload[fn]),
                            "home_path_hits_neutraled": n_home,
                            "literal_keys_found": 0,
                            "note": ("the CURRENT state: the acceptance-runs' "
                                     "engine reverted byte-exact (see "
                                     "GROQ-FLIP-RECEIPT.json in the prior "
                                     "Micah.zip); logic byte-identical except "
                                     "the owner-path placeholders")}
    print(f"[{fn}]: orig {orig_sha[:16]} -> sanitized "
          f"{receipt['files'][fn]['sha256_sanitized'][:16]} "
          f"(home-hits: {n_home}, keys: 0)")

man = ("ANDREW SOURCE-RECEIPT (the exact files the failed acceptance ran against)\n"
       + "\n".join(f"{receipt['files'][fn]['sha256_original']}  {fn} "
                   f"(as-used; for reconciliation-reference)"
                   for fn in FILES)
       + "\n\nSANITIZED DELIVERED:\n"
       + "\n".join(f"{receipt['files'][fn]['sha256_sanitized']}  {fn}.SANITIZED.py"
                   for fn in FILES)
       + "\n\nSANITIZE-SCOPE: (1) the owner home-path -> C:\\Users\\OWNER;"
         " (2) ZERO literal keys/tokens by scan (regex set in the build tool);"
         " (3) the LOGIC = byte-identical else (the hosts/ports/models/."
         "env-read patterns = preserved - the repair needs them).\n"
         "The flip-era diff (14fd9164...) = already receipted to Mica "
         "(Micah.zip 5a4499bf...).\n")

if os.path.exists(ZP):
    os.remove(ZP)
with zipfile.ZipFile(ZP, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in FILES:
        z.writestr("Micah-Recon/" + fn.replace(".py", ".SANITIZED.py"),
                   payload[fn])
    z.writestr("Micah-Recon/SHA256MANIFEST.txt", man)
    z.writestr("Micah-Recon/receipt.json",
               json.dumps(receipt, indent=1))
zh = hashlib.sha256(open(ZP, "rb").read()).hexdigest()
print(f"[zip] -> {ZP} ({os.path.getsize(ZP):,} bytes)")
print(f"[zip sha256]: {zh}")