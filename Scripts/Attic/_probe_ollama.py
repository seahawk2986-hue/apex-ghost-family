import os
import sys
import urllib.request
import json

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = open(os.path.join(ROOT, ".env"), encoding="utf-8-sig").read()
key = None
for ln in env.splitlines():
    if ln.strip().startswith("OLLAMA_API_KEY="):
        key = ln.split("=", 1)[1].strip().strip('"').strip("'")
print("key present:", bool(key), "| key length:", len(key or ""))
# the honest minimal probe against ollama's cloud API
for url in ("https://ollama.com/v1/chat/completions",
            "https://api.ollama.com/v1/chat/completions"):
    try:
        req = urllib.request.Request(
            url, data=json.dumps({
                "model": "gpt-oss:20b",
                "messages": [{"role": "user", "content": "Reply: OK"}],
                "max_tokens": 8}).encode(),
            headers={"Authorization": "Bearer " + (key or ""),
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode())
        txt = (d.get("choices", [{}])[0].get("message", {})
               .get("content", ""))
        print(f"{url} -> OK | answer: {txt[:20]!r}")
        break
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "code", 0)
        print(f"{url} -> {code or ''} {str(e)[:60]}")