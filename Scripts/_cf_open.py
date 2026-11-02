"""The Cloudflare Workers-AI door: token stored -> models-search -> live proof."""
import io
import json
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env"
KEY = "cfut_nsvRYJwjo86LJN11rxDyDPgLk7qMbUpVMAL1Hg5R4d8692b"
lines = [l for l in open(P, encoding="utf-8-sig").read().splitlines()
         if l.strip() and not l.startswith("CLOUDFLARE_API_TOKEN=")]
lines.append("CLOUDFLARE_API_TOKEN=" + KEY)
open(P, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("[env]: CLOUDFLARE_API_TOKEN stored")

import requests
AC = [l.split("=", 1)[1].strip() for l in open(P, encoding="utf-8-sig").read().splitlines()
      if l.startswith("CLOUDFLARE_ACCOUNT_ID=")][0]
print("[account]:", AC[:8] + "...")
H = {"Authorization": "Bearer " + KEY}
try:
    r = requests.get("https://api.cloudflare.com/client/v4/accounts/" + AC
                     + "/ai/models/search", headers=H, timeout=30)
    print("[models search]:", r.status_code)
    if r.status_code == 200:
        models = (r.json().get("result") or {}).get("models") or r.json().get("result") or []
        chat = [m.get("name", "?") for m in (models if isinstance(models, list) else [])
                if "function" not in str(m)[:60] and "embedding" not in str(m.get("name", "")).lower()]
        print("[served]:", len(chat))
        for i in chat[:18]:
            print("   ", i)
    else:
        print("   [head]:", r.text[:200])
except Exception as e:
    print("[search FAIL]:", type(e).__name__, str(e)[:80])

URL = ("https://api.cloudflare.com/client/v4/accounts/" + AC
       + "/ai/v1/chat/completions")   # openai-compatible
for model in ("@cf/meta/llama-3.1-8b-instruct", "@cf/qwen/qwen3-8b-instruct"):
    try:
        t0 = time.time()
        r = requests.post(URL, headers={**H, "Content-Type": "application/json"},
                          timeout=60,
                          json={"model": model, "max_tokens": 120,
                                "messages": [{"role": "user",
                                              "content": "Reply with one word: strong"}]})
        dt = round(time.time() - t0, 2)
        if r.status_code == 200:
            c = r.json()["choices"][0]["message"].get("content", "")
            print(f"[200] {model}: '{str(c).strip()[:40]}' wall={dt}s")
        else:
            print(f"[{r.status_code}] {model}: {r.text[:110]} wall={dt}s")
    except Exception as e:
        print("[FAIL]", model, ":", type(e).__name__, str(e)[:70])