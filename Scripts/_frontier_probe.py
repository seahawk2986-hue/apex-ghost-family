"""Frontier probe: unlock free doors that are already key'd but dark.
GitHub Models (3 route variants - kills the plain-OK mystery) +
Gemini free tier (the sleeping GEMINI key). 1-token probes, honest prints."""
import io
import json
import os
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = {}
for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
    if "=" in ln:
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()

GH = env.get("GITHUB_TOKEN", "")
print("=== GitHub Models probes (the OK-mystery) ===")
for label, method, url, headers, body in [
    ("catalog-api.github", "GET", "https://api.github.com/models",
     {"Authorization": "Bearer " + GH,
      "Accept": "application/vnd.github+json"}, None),
    ("catalog-models.github", "GET", "https://models.github.ai/catalog/models",
     {"Authorization": "Bearer " + GH, "Accept": "application/json"}, None),
    ("infer-models.github", "POST", "https://models.github.ai/chat/completions",
     {"Authorization": "Bearer " + GH, "Content-Type": "application/json"},
     {"model": "openai/gpt-4.1-mini", "max_tokens": 5,
      "messages": [{"role": "user", "content": "Say OK."}]}),
]:
    try:
        r = (requests.get(url, headers=headers, timeout=30) if method == "GET"
             else requests.post(url, headers=headers, json=body, timeout=60))
        ct = r.headers.get("content-type", "")[:30]
        print(f"[{label}]: HTTP {r.status_code} | ct={ct} | {r.text[:90]!r}")
    except Exception as e:
        print(f"[{label}]: {type(e).__name__} {str(e)[:80]}")

print("=== groq catalog (the kimi 404 - live model list, free) ===")
try:
    r = requests.get("https://api.groq.com/openai/v1/models",
                     headers={"Authorization": "Bearer " + env.get("GROQ_API_KEY", "")},
                     timeout=30)
    if r.status_code == 200:
        ids = [m.get("id") for m in r.json().get("data", [])]
        kimi = [i for i in ids if "kimi" in i.lower() or "moonshot" in i.lower()]
        print(f"[groq models]: {len(ids)} live | kimi-family: {kimi or '(GONE)'}")
        print(f"[groq sample]: {ids[:6]}")
    else:
        print(f"[groq models]: HTTP {r.status_code} | {r.text[:80]}")
except Exception as e:
    print("[groq models]:", type(e).__name__, str(e)[:80])

print("=== Gemini free tier (the sleeping key) ===")
gk = next((v for k, v in env.items() if k.startswith("GEMINI") and v), "")
if gk := gk:
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                         params={"key": gk}, timeout=45)
        print(f"[gemini-models]: HTTP {r.status_code}")
        if r.status_code == 200:
            names = [m.get("name", "") for m in r.json().get("models", [])]
            print(f"[gemini count]: {len(names)} | sample: {names[:3]}")
            # the 1-token generate proof on the cheapest always-free model
            for m in ("gemini-2.0-flash", "gemini-2.5-flash"):
                if "models/" + m in names:
                    g = requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{m}:generateContent?key={gk}",
                        json={"contents": [{"parts": [{"text": "Say OK."}]}],
                              "generationConfig": {"maxOutputTokens": 8}},
                        timeout=45)
                    txt = ""
                    if g.status_code == 200:
                        try:
                            txt = (g.json()["candidates"][0]["content"]
                                   ["parts"][0]["text"])[:30]
                        except Exception:
                            txt = "(200 but shape differs)"
                    print(f"[gemini {m}]: HTTP {g.status_code} | {txt}")
                    break
        else:
            print("[gemini-models]:", r.text[:110])
    except Exception as e:
        print("[gemini]:", type(e).__name__, str(e)[:80])
else:
    print("[gemini]: no GEMINI* key in .env")