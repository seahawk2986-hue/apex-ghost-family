"""Gemini final avenues: v1 (not v1beta) + the lite/8b variants + SSE shape.
The key = proven valid (list = 200). If generate stays 404 on every version,
the door = plan/region-gated - an honest founder-note, not a silent skip."""
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
GK = next((v for k, v in env.items() if k.startswith("GEMINI") and v), "")

BASES = ["https://generativelanguage.googleapis.com/v1beta",
         "https://generativelanguage.googleapis.com/v1"]
MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]
for base in BASES:
    for m in MODELS if (MODELS := MODELS) else []:
        pass
for base in BASES:
    for m in MODELS:
        try:
            g = requests.post(
                f"{base}/models/{m}:generateContent",
                headers={"x-goog-api-key": GK,
                         "Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "Say OK."}]}],
                      "generationConfig": {"maxOutputTokens": 8}},
                timeout=40)
            note = g.text[:80].replace("\n", " ") if g.status_code != 200 else ""
            print(f"[{base.split('/')[-1]} {m}]: HTTP {g.status_code} {note}")
            if g.status_code == 200:
                print("[door]: OPEN -", g.text[:120])
                break
        except Exception as e:
            print(f"[{base.split('/')[-1]} {m}]:", type(e).__name__, str(e)[:70])
    else:
        continue
    break