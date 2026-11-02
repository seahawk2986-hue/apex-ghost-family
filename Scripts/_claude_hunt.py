"""The Claude door hunt: every claude entry in the live catalog + free status,
plus a same-shape hunt for grok/deepseek/qwen3-max/llama-4-class free doors."""
import io
import json
import os
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
with urllib.request.urlopen("https://openrouter.ai/api/v1/models",
                            timeout=30) as r:
    models = json.loads(r.read())["data"]

FAMS = ("claude", "grok", "gpt-5", "qwen", "deepseek")
for fam in FAMS:
    hits = [m for m in models if fam in m["id"].lower()]
    free_hits = [m for m in hits
                 if ":free" in m["id"]
                 or str(m.get("pricing", {}).get("prompt", "1")) == "0"]
    print(f"[{fam}]: {len(hits)} entries | free doors: {len(free_hits)}")
    for m in free_hits:
        print("   [FREE]", m["id"])

claude = [m for m in models if "claude" in m["id"].lower()]
print("[claude lineup (priced)]:")
for m in claude[:10]:
    p = m.get("pricing", {}).get("prompt", "?")
    ctx = m.get("context_length") or 0
    print(f"   {m['id']}  ctx={ctx//1000}k  prompt=${p}/tok")

free_all = sorted(m["id"] for m in models if ":free" in m["id"])
print("[total free doors today]:", len(free_all))