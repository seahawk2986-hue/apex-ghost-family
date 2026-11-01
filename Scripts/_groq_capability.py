"""THE GPT-OSS-120B CAPABILITY GATE (the test-and-test law): a REAL
diff-review x2 + the rate-shape + the latency. Receipts: the router's
decision evidence. $0 enforced."""
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
     "User-Agent": "apex-free-tier/1.0 (+github.com/seahawk2986-hue)"}
MODEL = "openai/gpt-oss-120b"
DIFF_LINES = [
    "--- a/hooks/muse/provider_dummy.py",
    "+++ b/hooks/muse/provider_dummy.py",
    "@@ -1,3 +1,6 @@",
    " from pathlib import Path",
    "+",
    " def load(p):",
    "-    return Path(p).read_text()",
    "+    p = Path(p)",
    "+    if not p.exists():",
    "+        raise FileNotFoundError(p)",
    "+    return p.read_text()",
]
DIFF = "\n".join(DIFF_LINES)
REAL_ASK = ("Review this automated contribution BEFORE it ships.\n"
            "ISSUE: the provider's load() should fail loudly on a missing "
            "file.\nDIFF:\n" + DIFF +
            '\n\nJudge: (1) scope, (2) obvious errors, (3) style. Reply '
            'ONLY JSON: {"ship": true/false, "why": "<=150 chars"}')
out = {"runs": [], "ok_json": 0, "latency_s": []}


def call(prompt):
    t0 = time.time()
    body = {"model": MODEL, "messages": [{"role": "user",
                                          "content": prompt}],
            "temperature": 0, "max_tokens": 250}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers=H, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        out["latency_s"].append(round(time.time() - t0, 2))
        c = (d.get("choices") or [{}])[0].get("message", {}).get("content",
                                                                 "")
        has = '"ship"' in c
        out["ok_json"] += 1 if has else 0
        out["runs"].append({"verdict": has, "chars": len(c),
                            "sample": c[:110]})
        return c
    except Exception as e:
        b = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        out["runs"].append({"err": e.__class__.__name__ + " " +
                            (b or b"")[:90], "at":
                            round(time.time() - t0, 2)})
        return None


c1 = call(REAL_ASK)
time.sleep(2)
c2 = call(REAL_ASK)
for i in range(3):
    call('Reply ONLY JSON: {"n": ' + str(i + 1) + "}.")
    time.sleep(1)
print(f"[capability] ok_json {out['ok_json']}/{len(out['runs'])} | "
      f"latency {out['latency_s']}")
for r in out["runs"][:3]:
    print("  run:", json.dumps(r, ensure_ascii=False)[:128])
with open(os.path.join(ROOT, "Config", "groq_120b_capability.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "model": MODEL,
               "price": "0.00 (the free tier; no card attached)",
               "local_ram_gb": 0.0, **out}, f, ensure_ascii=False, indent=1)