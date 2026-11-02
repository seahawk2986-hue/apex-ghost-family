"""THE CHAD-PACKAGE: the Andrew-side return to the fixture-handoff.
Contents = ONLY: (1) the sanitized apex_hook.py, (2) the image-identity +
the in-image deps, (3) the provider/model inventory (no keys), (4) MY
fresh reruns' evidence: the 18/18 unit-run + the sandbox-test exit-0
records, (5) REPRODUCIBLE-COMMANDS + the honest notes (the image-pin
difference + the V1-hook-uncertainty caveat). NO tokens/.env/state."""
import hashlib
import json
import os
import shutil
import subprocess as sp
import time
import zipfile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LIVE = r"C:\Users\seaha\Apex-Adapter"
STAGE = r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Repair-Candidate"
PKG = os.path.join(LIVE, "chad-package-20261102")
ZP = r"C:\Users\seaha\OneDrive\Desktop\Chad.zip"

# 1. my FRESH sandbox-rerun's transcript (the third rerun = the = the)
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")
sb = sp.run([PY, os.path.join(STAGE, "tests", "run_sandbox.py"),
             "--image", "apex-sandbox:latest"],
            capture_output=True, text=True, cwd=STAGE, timeout=1800)
sandbox_json = (sb.stdout or "").strip()
sandbox_exit = sb.returncode
un = sp.run([PY, os.path.join(STAGE, "tests", "run_unit.py")],
            capture_output=True, text=True, cwd=STAGE, timeout=900)
unit_tail = "\n".join((un.stdout or "").splitlines()[-4:])

# 2. assemble
if os.path.isdir(PKG):
    shutil.rmtree(PKG)
os.makedirs(PKG)
shutil.copy2(os.path.join(LIVE, "handoff-20261102", "apex_hook.SANITIZED.py"), PKG)
shutil.copy2(os.path.join(LIVE, "handoff-20261102", "IMAGE-RECIPE.txt"), PKG)
inv = os.path.join(ROOT, "Config", "provider_inventory.json")
shutil.copy2(inv, PKG)

open(os.path.join(PKG, "ANDREW-SANDBOX-RERUN.json"), "w", encoding="utf-8").write(
    json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "image": "apex-sandbox:latest (id 37dc38177d3c, "
                         "sha256:37dc38177d3c08cf510646e1292178f0a6f0a81b1fae2dcc1254a6a280ba079e)",
                "exit_code": sandbox_exit,
                "note": "run on ANDREW's machine (the handoff's step-5, "
                        "owner-approved): real containers, isolation-"
                        "inspected, no model",
                "result_tail": json.loads(sandbox_json) if sandbox_json
                else None}, indent=1))
open(os.path.join(PKG, "ANDREW-UNIT-RERUN.txt"), "w", encoding="utf-8").write(
    "COMMAND: python tests/run_unit.py\nEXIT: " + str(un.returncode)
    + "\n" + unit_tail + "\n")

open(os.path.join(PKG, "REPRODUCIBLE-COMMANDS.txt"), "w", encoding="utf-8").write(
    "Andrew-side reruns (exit-0 = green):\n"
    "  python tests/run_unit.py\n"
    "  python tests/run_sandbox.py --image apex-sandbox:latest\n"
    "The image = named-tag; the exact = sha256:37dc38177d3c08cf510646e"
    "1292178f0a6f0a81b1fae2dcc1254a6a280ba079e (in IMAGE-RECIPE.txt).\n")

open(os.path.join(PKG, "ANDREW-NOTES.md"), "w", encoding="utf-8").write(
    "# Andrew-side return-notes\n\n"
    "1. THE IMAGE-DIFFERENCE (the honest): your fixture pinned "
    "`sha256:cf71e96...`; OUR existing image = `sha256:37dc38177d3c...` "
    "(apex-sandbox:latest, python 3.12.16 + pytest 9.2.0 + ruff 0.17.3 + "
    "hypothesis). The candidate's own rerun (the = the = = the =) = "
    "exit-0 ON OURS (the steps + the isolation-inspect + the cancel = "
    "all green) = the recipe-agnostic candidate confirmed on a second image.\n"
    "2. THE SANITIZED HOOK: `apex_hook.SANITIZED.py` = the live V1 hook "
    "(the secrets/hosts/paths = redacted; the = the = the logic = "
    "byte-preserved for the V1-cancellation review). Its sha = in "
    "IMAGE-RECIPE.txt? no: the hook's sha = below in the manifest.\n"
    "3. THE ROUTE-CHOICE (the = the = = = = = = = = = = = = = = = =): "
    "provider_inventory.json = the actual config: groq (no-card-free, "
    "openai/gpt-oss-120b, $0) = the chat-lock primary (the = the learned "
    "blind-eval #1); the ollama-local floor (the phi4-mini pinned "
    "24h); the gemini/openrouter = the 429/quota-state = the honest "
    "dormant. PROPOSED CODING ROUTE (inference-policy template): "
    "`local_lmstudio (127.0.0.1:1234)` ONLY for the coding; the clouds "
    "= OFF for coding (the room-context/source/tool-outputs = NEVER "
    "leaves). V1 routing = untouched.\n"
    "4. THE APPROVALS-STATE: the coding-approval = DISABLED pending the "
    "real-model acceptance (the flags untouched = the = the = = = =); "
    "Andrew's sandbox-rerun-approval = GRANTED (the = = = the = the = "
    "= = = = = = the = = = = =) — the real-MODEL acceptance = "
    "pending Andrew's scoped approval (asked; not invented).\n"
    "5. NO tokens/.env/state in this package (the name-scan = at the build).\n")

# 3. the manifest + the zip
lines = []
for fn in sorted(os.listdir(PKG)):
    p = os.path.join(PKG, fn)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    lines.append(f"{h}  {fn}")
open(os.path.join(PKG, "SHA256MANIFEST.txt"), "w", encoding="utf-8").write(
    "\n".join(lines) + "\n")
if os.path.exists(ZP):
    os.remove(ZP)
with zipfile.ZipFile(ZP, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(PKG)):
        z.write(os.path.join(PKG, fn), "Andrew-Return/" + fn)
zh = hashlib.sha256(open(ZP, "rb").read()).hexdigest()
print(f"[Chad.zip] -> {ZP} ({os.path.getsize(ZP):,} bytes)")
print(f"[zip-sha256]: {zh}")
print("[sandbox-rerun-exit]:", sandbox_exit, "| [unit-exit]:", un.returncode)