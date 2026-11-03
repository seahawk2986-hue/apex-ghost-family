"""One-token lane probes: alive / rate-walled / credit-dead - honest evidence."""
import io
import json
import os
import sys

import requests

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = {}
for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
    if "=" in ln:
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()

PROBES = [
    ("sflow-122b", "https://api.siliconflow.com/v1/chat/completions",
     "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B"),
    ("or-ultra", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("groq-120b", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b"),
]

for name, url, k, model in PROBES:
    try:
        r = requests.post(url,
                          headers={"Authorization": "Bearer " + env[k],
                                   "Content-Type": "application/json"},
                          json={"model": model, "max_tokens": 8, "temperature": 0.0,
                                "messages": [{"role": "user", "content": "Say OK."}]},
                          timeout=45)
        body = r.text[:90].replace("\n", " ")
        print(f"[{name}]: HTTP {r.status_code} | {body}")
    except Exception as e:
        print(f"[{name}]: {type(e).__name__} {str(e)[:80]}")