import json
import os
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
key = None
for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
    if ln.strip().startswith("OLLAMA_API_KEY="):
        key = ln.split("=", 1)[1].strip().strip('"').strip("'")
for model in ("gpt-oss:120b", "gpt-oss:20b"):
    try:
        req = urllib.request.Request(
            "https://ollama.com/v1/chat/completions",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user",
                              "content": "Reply with exactly: OK"}],
                "max_tokens": 300}).encode(),
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        msg = d.get("choices", [{}])[0].get("message", {})
        print(f"{model}: content={msg.get('content', '')[:30]!r} "
              f"| reasoning={len(str(msg.get('reasoning') or ''))} chars "
              f"| usage={d.get('usage')}")
    except Exception as e:
        print(f"{model} -> {str(e)[:70]}")