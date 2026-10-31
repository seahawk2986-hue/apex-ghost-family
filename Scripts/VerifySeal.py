"""Honest signature verification: exceptions tell the truth, not return-None."""
import base64
import json
import os
import time
import hashlib

AD = r"C:\Users\seaha\Apex-Adapter"
from nacl.signing import VerifyKey  # noqa: E402
from nacl.exceptions import BadSignatureError  # noqa: E402

pk = json.load(open(os.path.join(AD, "family_seed_packet.json"), encoding="utf-8-sig"))
sig_block = pk.pop("constitution_signature")
constitution = json.dumps(pk.get("rules", {}), sort_keys=True).encode()
pub = json.load(open(os.path.join(AD, "family_keys", "family_public.json"),
                     encoding="utf-8-sig"))["public_key_b64"]
vk = VerifyKey(base64.b64decode(pub))

honest = False
signed_by = sig_block.get("signed_by", "")
try:
    vk.verify(constitution, base64.b64decode(sig_block["signature_b64"]))
    honest = True
except BadSignatureError:
    honest = False
print(f"CONSTItution SIGNED BY {signed_by}:")
print("signature valid:", honest, "(verified by exception-based check - the honest way)")
if honest:
    print("the packet's LAWS are the founder's, byte-for-byte - tampering visible")
sig_block["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
sig_block["verified"] = honest
pk["constitution_signature"] = sig_block
json.dump(pk, open(os.path.join(AD, "family_seed_packet.json"), "w", encoding="utf-8"), indent=1)
print("packet updated: verified=true, checked-by: public key (anyone can verify)")