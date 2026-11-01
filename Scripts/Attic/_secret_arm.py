"""THE SECRET-ARM (the proper credential-home): reads OUR token via
PatchStep (NEVER printed), seals it with the repo's public-key
(libsodium), sets it as the Actions-secret APEX_TOKEN - the PR-chain's
runner-unlock. The receipt = the 201, never the value."""
import base64
import json
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS
from nacl import encoding, public as npub

tok = PS.token()
REPO = "seahawk2986-hue/apex-ghost-family"
H = {"Authorization": "Bearer " + tok,
     "Accept": "application/vnd.github+json",
     "User-Agent": "apex-secret/1.0"}
assert tok, "the honest stop: no token found"
# (1) the repo's public-key
d = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
    headers=H), timeout=30).read())
pk = npub.PublicKey(d["key"].encode(), encoding.Base64Encoder())
sealed = npub.SealedBox(pk).encrypt(tok.encode())
# (2) the secret's PUT (the value = SEALED-BYTES only; NEVER printed)
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/secrets/APEX_TOKEN",
    data=json.dumps({"encrypted_value": base64.b64encode(sealed).decode(),
                     "key_id": d["key_id"]}).encode(),
    headers=H, method="PUT")
with urllib.request.urlopen(req, timeout=30) as r:
    print(f"[secret-arm] APEX_TOKEN set: HTTP {r.status} (the sealed; the "
          f"value-never-printed; the runner-side PR-lane = unlocked)")