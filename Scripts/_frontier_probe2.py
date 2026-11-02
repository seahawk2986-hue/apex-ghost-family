"""Frontier round 2: org-scoped GitHub Models inference + Gemini header-auth
generate + full groq list (the kimi replacement pick). All 1-token, free."""
import io
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
GK = next((v for k, v in env.items() if k.startswith("GEMINI") and v), "")

print("=== identity check (free, tells us if the PAT = valid) ===")
try:
    r = requests.get("https://api.github.com/user",
                     headers={"Authorization": "Bearer " + GH,
                              "Accept": "application/vnd.github+json"}, timeout=30)
    if r.status_code == 200:
        login = r.json().get("login")
        print("[identity]:", login)
        OWNER = login
    else:
        print("[identity]: HTTP", r.status_code, r.text[:70])
        login = "seahawk2986-hue"
except Exception as e:
    print("[identity]:", type(e).__name__, str(e)[:80])
    login = "seahawk2986-hue"

print("=== GitHub Models: org-scoped inference (the last documented variant) ===")
for label, url, body in [
    ("org-infer", f"https://models.github.ai/{login}/chat/completions",
     {"model": "openai/gpt-4.1-mini", "max_tokens": 5,
      "messages": [{"role": "user", "content": "Say OK."}]}),
    ("models-ai-infer", "https://models.github.ai/openai/gpt-4.1-mini/chat/completions",
     {"max_tokens": 5, "messages": [{"role": "user", "content": "Say OK."}]}),
]:
    try:
        r = requests.post(url, json=body,
                          headers={"Authorization": "Bearer " + GH,
                                   "Content-Type": "application/json",
                                   "Accept": "application/vnd.github+json"},
                          timeout=45)
        print(f"[{label}]: HTTP {r.status_code} | ct={r.headers.get('content-type', '')[:24]} "
              f"| {r.text[:80]!r}")
    except Exception as e:
        print(f"[{label}]:", type(e).__name__, str(e)[:80])

print("=== Gemini generate retry (header auth) ===")
for m in ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"):
    try:
        g = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
            headers={"x-goog-api-key": GK, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "Say OK."}]}],
                  "generationConfig": {"maxOutputTokens": 8}}, timeout=45)
        txt = ""
        if g.status_code == 200:
            try:
                txt = g.json()["candidates"][0]["content"]["parts"][0]["text"][:30]
            except Exception:
                txt = "(200, shape differs)"
        print(f"[{m}]: HTTP {g.status_code} | {txt}")
        if g.status_code == 200 and txt:
            break
    except Exception as e:
        print(f"[{m}]:", type(e).__name__, str(e)[:80])

print("=== groq full live list (kimi replacement pick) ===")
try:
    r = requests.get("https://api.groq.com/openai/v1/models",
                     headers={"Authorization": "Bearer " + env.get("GROQ_API_KEY", "")},
                     timeout=30)
    if r.status_code == 200:
        print([m.get("id") for m in r.json().get("data", [])])
except Exception as e:
    print("[groq]:", type(e).__name__, str(e)[:80])