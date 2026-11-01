"""THE CONTEXT-BAND PROBE: find the free tier's REAL request-band (the
sizes ladder) - the honest number before setting CloudBrain's budgets."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from CloudBrain import env_keys

KEY = env_keys().get("GROQ_API_KEY", "")
URL = "https://api.groq.com/openai/v1/chat/completions"
H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
     "User-Agent": "apex-free-tier/1.0"}
BAND = {}
for size in (6000, 9000, 12000, 16000):
    body = {"model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content":
                          ("filler line for the band probe\n" * (size // 24))
                          + 'Reply ONLY JSON {"seen": ' + str(size) + "}"}],
            "max_tokens": 30}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers=H, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        BAND[size] = "OK"
    except Exception as e:
        BAND[size] = (e.__class__.__name__ + " " + str(getattr(
            getattr(e, "fp", None), "code", 0)))
    time.sleep(1)
print("[band] " + json.dumps(BAND))
with open(os.path.join(ROOT, "Config", "groq_context_band.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "band_sizes": BAND,
               "law": "the honest budget = the measured band, never the "
                      "advertised maximum"}, f, ensure_ascii=False, indent=1)