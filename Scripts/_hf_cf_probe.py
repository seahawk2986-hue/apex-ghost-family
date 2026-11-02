"""HF + Cloudflare probes: the two keys without lanes - honest verdicts."""
import io
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
env = {}
for l in open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env",
              encoding="utf-8-sig"):
    if "=" in l:
        k, v = l.split("=", 1)
        env[k.strip()] = v.strip()

# 1) HuggingFace Inference (the router): which free models = callable?
try:
    r = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={"Authorization": "Bearer " + env.get("HF_TOKEN", ""),
                 "Content-Type": "application/json"},
        json={"model": "meta-llama/Llama-3.2-1B-Instruct", "max_tokens": 8,
              "messages": [{"role": "user", "content": "Say OK."}]}, timeout=45)
    print("[hf-inference]: HTTP", r.status_code, "|", r.text[:90])
except Exception as e:
    print("[hf-inference]:", type(e).__name__, str(e)[:80])

# 2) Cloudflare token: fresh re-check (the old cfut-... = 401 in the past)
try:
    r2 = requests.get(
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        headers={"Authorization": "Bearer " + env.get("CLOUDFLARE_API_TOKEN", "")},
        timeout=45).json()
    print("[cf token]:", r2.get("success"), "|",
          str(r2.get("messages", ""))[:70])
except Exception as e:
    print("[cf]:", type(e).__name__, str(e)[:80])