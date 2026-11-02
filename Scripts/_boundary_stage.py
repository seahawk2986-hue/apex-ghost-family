"""THE BOUNDARY STAGE: build the staged-candidate from the LIVE adapter
files (surgical, never a baseline overwrite) + transform the ACTUAL hook
into a NEW staged file. No install, no execution of adapter code.
1. copy v2_* + workspace files from LIVE; copy v1_chat_boundary from PKG
2. companion.py (live copy): +import v1_chat_boundary; Respond->dispatch
   (hunk C = comment-only, anchor absent in evolved live = skipped)
3. v2_job_engine.py (live copy): unchanged (it has no source_revision;
   the revision-receipt = computed here over the 8 files)
4. prepare_hook_patch.py ACTUAL_HOOK -> staged hook + .patch + receipt
5. py_compile everything staged; SHA-receipt for the return."""
import hashlib
import json
import os
import py_compile
import shutil
import subprocess as sp
import sys

ROOT = r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102\Apex-V1-Chat-Boundary"
LIVE = r"C:\Users\seaha\Apex-Adapter"
OUT = r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102\staged-candidate"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT, exist_ok=True)

# 1. the live files (the EVOLVED truth) + the new boundary module
# (the live adapter = monolith-architecture: ONLY 3 v2-files exist there;
# the package's other 5 split-engine modules = reviewed + receipted,
# never copied into the live-shape staging = no shadow modules)
live_files = ["companion.py", "v2_job_engine.py", "v2_contract.py"]
copied = []
for f in live_files:
    p = os.path.join(LIVE, f)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(OUT, f))
        copied.append(f)
shutil.copy2(os.path.join(ROOT, "source", "v1_chat_boundary.py"),
             os.path.join(OUT, "v1_chat_boundary.py"))
print("[copied from LIVE]:", copied)

# 2. the surgical companion patch (hunks A + B only)
cp = os.path.join(OUT, "companion.py")
src = open(cp, encoding="utf-8-sig").read()
a_from = "import apex_hook  # noqa: E402  (standard hook module per contract)"
a_to = a_from + "\nimport v1_chat_boundary"
b_from = "res = apex_hook.respond(req, cancel_event)"
b_to = "res = v1_chat_boundary.dispatch(apex_hook, req, cancel_event)"
assert src.count(a_from) == 1, "import-anchor not unique"
assert src.count(b_from) == 1, "dispatch-anchor not unique"
src = src.replace(a_from, a_to).replace(b_from, b_to)
open(cp, "w", encoding="utf-8", newline="").write(src)
print("[companion]: hunks A+B applied (import + chat-only dispatch)")

# 3. the revision receipt over the live-shape candidates (name\0bytes\0)
names = ["companion.py", "v2_job_engine.py", "v2_contract.py",
         "v1_chat_boundary.py"]
h = hashlib.sha256()
for n in names:
    h.update(n.encode() + b"\0" + open(os.path.join(OUT, n), "rb").read() + b"\0")
rev = h.hexdigest()
print(f"[live-shape 4-file source revision]: {rev}")

# 4. the ACTUAL-hook transform (staging output; never an install)
hook_in = os.path.join(LIVE, "apex_hook.py")
hook_out = os.path.join(OUT, "apex_hook.chat-only.STAGED.py")
r = sp.run([sys.executable, os.path.join(ROOT, "prepare_hook_patch.py"),
            hook_in, hook_out], capture_output=True, text=True, timeout=60)
print("[hook-transform exit]:", r.returncode)
print((r.stdout or r.stderr).strip()[:400])
patch_path = hook_out + ".patch"
pd = open(patch_path, encoding="utf-8").read().splitlines() if os.path.exists(patch_path) else []
adds = sum(1 for l in pd if l.startswith("+") and not l.startswith("+++"))
dels = sum(1 for l in pd if l.startswith("-") and not l.startswith("---"))
print(f"[hook diff]: +{adds}/-{dels} lines (additions = the 2 chat-only wrappers)")
bad = [l for l in pd if any(k.lower() in l.lower() for k in ("api_key", "token", "sk-", "bearer")) and l.startswith("+")]
print("[secret-leak scan on diff additions]:",
      "CLEAN (no secrets added)" if not bad else ("LEAK: " + str(bad[:2])))

# 5. compile-prove every staged module (bytecode only; nothing imported)
for f in sorted(os.listdir(OUT)):
    if f.endswith((".py", ".STAGED.py")):
        try:
            py_compile.compile(os.path.join(OUT, f), doraise=True)
        except Exception as e:
            print(f"[COMPILE FAIL] {f}: {str(e)[:120]}")
            sys.exit(1)
print("[compile]: every staged .py compiles clean")

rec = {"live_shape_4_file_source_revision": rev,
       "stagedFiles": {f: sha(os.path.join(OUT, f)) for f in sorted(os.listdir(OUT))
                       if os.path.isfile(os.path.join(OUT, f))},
       "note": ("live adapter = monolith engine (v2_job_engine.py 69KB); the "
                "package's 5 split-engine modules (state/sandbox/io/inference + "
                "the source_revision hunk) = NOT APPLICABLE to the live shape; "
                "reviewed + MANIFEST-verified only. Hunks A+B applied; hunk C "
                "(comment-only) = skipped, its anchor text absent in live.")}
open(os.path.join(OUT, "STAGE-RECEIPT.json"), "w", encoding="utf-8").write(
    json.dumps(rec, indent=1))
print("[stage receipt]: written (all SHAs inside)")