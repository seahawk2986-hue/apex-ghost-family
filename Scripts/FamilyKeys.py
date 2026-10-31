"""THE FAMILY KEYS: real cryptographic provenance (ed25519 via pynacl).

The founder signs the constitution ONCE; every packet/manifest/conversion
carries verifiable signatures. The private key belongs to the family's
founding moment (stored owner-side); the public key travels publicly.
"""
import base64
import hashlib
import json
import os
import subprocess
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"

r = subprocess.run([PY, "-m", "pip", "install", "pynacl", "--quiet",
                    "--disable-pip-version-check"], capture_output=True, text=True, timeout=180)
print("pynacl install:", (r.stdout or "").strip().splitlines()[-1] if r.stdout else "ok/no-output")

KEYS = os.path.join(AD, "family_keys")
os.makedirs(KEYS, exist_ok=True)
PUB = os.path.join(KEYS, "family_public.json")
PRIV = os.path.join(KEYS, "family_private.bin")

from nacl.signing import SigningKey  # noqa: E402

if not os.path.isfile(PRIV):
    sk = SigningKey.generate()
    open(PRIV, "wb").write(bytes(sk))
    pub = base64.b64encode(bytes(sk.verify_key)).decode()
    json.dump({"public_key_b64": pub, "algorithm": "ed25519",
               "created": time.strftime("%Y-%m-%d %H:%M:%S"),
               "owner": "Andrew Hike", "note": "the family's founding key"}, open(PUB, "w"), indent=1)
    print("NEW FAMILY KEYPAIR created (public in " + PUB + ")")
else:
    sk = SigningKey(open(PRIV, "rb").read())
    print("family keys exist - loaded")

pk = json.load(open(os.path.join(AD, "family_seed_packet.json"), encoding="utf-8-sig"))
constitution = json.dumps(pk.get("rules", {}), sort_keys=True).encode()
sig = sk.sign(constitution)
pkt_sig = base64.b64encode(sig.signature).decode()
pk["constitution_signature"] = {"algorithm": "ed25519",
                                "signature_b64": pkt_sig,
                                "signed_by": "Andrew Hike (founding key)",
                                "signs": hashlib.sha256(constitution).hexdigest()[:16]}
json.dump(pk, open(os.path.join(AD, "family_seed_packet.json"), "w", encoding="utf-8"), indent=1)

# verification (the public, anyone-checkable path)
vk = sk.verify_key
ver = vk.verify(constitution, base64.b64decode(pkt_sig))
print("constitution SIGNED + VERIFIED: ed25519 signature valid:", ver is None)
print("packet now carries: constitution_signature (owner: Andrew Hike)")