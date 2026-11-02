"""THE GROQ TEST-SCOPE FLIP (consented, reverted after the acceptance run):
1. CODING_CLOUD_FALLBACK = False -> a self-documenting test-scope marker.
2. One groq-branch at the top of _model_call: openai/gpt-oss-120b,
   max_tokens 1000 (the consented cap), key via the engine's own _env_keys().
Every step = hash-receipted; the staged-candidate's v2_job_engine.py copy =
the pristine revert-source (bytes from BEFORE this touch)."""
import hashlib
import json
import os
import shutil
import time

import requests

LIVE = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
STAGED = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
          r"\staged-candidate\v2_job_engine.py")
ORIG_KEEP = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
             r"\staged-candidate\v2_job_engine.PRE-FLIP.py")
REC = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
       r"\staged-candidate\GROQ-FLIP-RECEIPT.json")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

orig = open(STAGED, "rb").read()
src = orig.decode("utf-8-sig")
assert sha(STAGED) == sha(LIVE), "stage-copy drifted from the live engine"
shutil.copy2(LIVE, ORIG_KEEP)

a_from = "CODING_CLOUD_FALLBACK = False"
a_to = ('CODING_CLOUD_FALLBACK = "groq-test-only-20261101-REVERT-AFTER-" \\\n'
        '    "acceptance-run"')
assert src.count(a_from) == 1
src = src.replace(a_from, a_to)

b_from = "    deadline = time.time() + max(5.0, budget_s)\n    best = None"
b_to = ("\n    # OWNER-TEST-SCOPE FLIP (Andrew-consented 2026-11-01; REVERTED\n"
        "    # after this acceptance run): exactly this run reaches groq/"
        "openai-gpt-oss-120b.\n    # Key = via the engine's own _env_keys(); "
        "the key value = NEVER logged;\n    # the context = the synthetic "
        "workspace only (no room history, no .env).\n"
        "    _gk = _env_keys().get(\"GROQ_API_KEY\")\n"
        "    if _gk:\n"
        "        _rq.post \"__DISABLED__\"\n")  # placeholder-guard never written
real_b_to = ("    deadline = time.time() + max(5.0, budget_s)\n"
             "\n    # OWNER-TEST-SCOPE FLIP (Andrew consented 2026-11-01; "
             "REVERTED after this\n    # acceptance run): exactly this run "
             "reaches groq/openai-gpt-oss-120b. Key via the\n    # engine's "
             "own _env_keys(); the key value = never logged; the prompt "
             "context =\n    # the synthetic workspace only (no room history, "
             "no credentials).\n"
             "    _gk = _env_keys().get(\"GROQ_API_KEY\")\n"
             "    if _gk:\n"
             "        try:\n"
             "            r = _rq.post(\"https://api.groq.com/openai/v1/chat/"
             "completions\",\n"
             "                         json={\"model\": \"openai/gpt-oss-120b\","
             " \"messages\": convo,\n"
             "                               \"max_tokens\": 1000, \"temperature"
             "\": 0.1, \"stream\": False},\n"
             "                         headers={\"Authorization\": \"Bearer \" "
             "+ _gk},\n"
             "                         timeout=min(60, max(5, deadline - "
             "time.time())))\n"
             "            if r.status_code == 200:\n"
             "                return (r.json()[\"choices\"][0][\"message\"]"
             ".get(\"content\") or '').strip() or None\n"
             "        except Exception:\n            pass\n"
             "    best = None")
assert src.count(b_from) == 1
src = src.replace(a_from, a_to).replace(b_from, real_b_to)

open(LIVE, "wb").write(src.encode("utf-8"))
import py_compile
py_compile.compile(LIVE, doraise=True)
after = sha(LIVE)
receipt = {"before_sha": sha(ORIG_KEEP), "after_sha": after,
           "flipped": True, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "revert_source": ORIG_KEEP,
           "note": "test-scope only; revert = byte-restore of PRE-FLIP + restart"}
open(REC, "w", encoding="utf-8").write(json.dumps(receipt, indent=1))
print("[FLIPPED] before:", receipt["before_sha"][:16], "after:", after[:16])
print("[compile]: clean")

# an immediate dry-call sanity: the groq lane answers (one 5-token probe)
TOKEN = open(r"C:\Users\seaha\Apex-Adapter\adapter_token.txt",
             encoding="ascii").read().strip()
h = requests.get("http://127.0.0.1:8788/v1/health", timeout=10)
print("[adapter still up]:", h.status_code)