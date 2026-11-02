"""The NIM live probe: the three current models, one honest call each."""
import io
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
key = open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env",
           encoding="utf-8-sig").read().split("NVIDIA_API_KEY=")[1].splitlines()[0]
for model in ("moonshotai/kimi-k2.6", "deepseek-ai/deepseek-v4.1-flash",
              "z-ai/glm-5.3-flash"):
    try:
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                          headers={"Authorization": "Bearer " + key,
                                   "Content-Type": "application/json"},
                          json={"model": model, "max_tokens": 25,
                                "messages": [{"role": "user",
                                              "content": "Say OK and nothing else."}]},
                          timeout=120)
        if r.status_code == 200:
            c = r.json()["choices"][0]["message"]
            print("[%s]: 200 ALIVE | %r" % (model, str(c.get("content"))[:40]))
        else:
            print("[%s]: HTTP %s | %s" % (model, r.status_code, r.text[:90]))
    except Exception as e:
        print("[%s]:" % model, type(e).__name__, str(e)[:80])