"""THE 120B KNOB-BENCH (the utilize-better directive): the four levers
tested LIVE on the free tier ($0.00, no card):
 K1 the JSON-mode (response_format json_object) = the parse-proof verdicts
 K2 the reasoning_effort high = the deeper review-whys
 K3 the LONG-prompt band (30k chars) = the 131k-context's real use
 K4 the threaded 5-parallel vote = the wall-time utilization
Receipts: Config/groq_120b_knobs.json."""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from CloudBrain import env_keys

KEY = env_keys().get("GROQ_API_KEY", "")
URL = "https://api.groq.com/openai/v1/chat/completions"
H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
     "User-Agent": "apex-free-tier/1.0"}
M = "openai/gpt-oss-120b"
K = {}


def post(body, timeout=90):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def content(d):
    return (d.get("choices") or [{}])[0].get("message", {}).get("content", "")


# K1: the JSON-mode
try:
    d = post({"model": M, "messages": [{"role": "user", "content":
              'Review a one-line docstring fix. Reply JSON {"ship": true/'
              'false, "why": "<=140 chars"}'}],
              "response_format": {"type": "json_object"}, "temperature": 0,
              "max_tokens": 200})
    c = content(d)
    K["k1_json_mode"] = {"ok": json.JSONDecoder().raw_decode(c.strip()) is
                         not None, "note": c[:90]}
except Exception as e:
    K["k1_json_mode"] = {"ok": False, "note": str(e)[:90]}
# K2: the reasoning-effort
try:
    t0 = time.time()
    d = post({"model": M, "messages": [{"role": "user", "content":
              'Review: a patch raises FileNotFoundError in load() on a '
              'missing file. Judge scope/errors/style. Reply ONLY JSON '
              '{"ship": true, "why": "<=140 chars"}'}],
              "reasoning_effort": "high", "max_tokens": 500})
    c = content(d)
    K["k2_reasoning"] = {"ok": '"ship"' in c, "latency_s":
                         round(time.time() - t0, 2), "note": c[:110]}
except Exception as e:
    K["k2_reasoning"] = {"ok": False, "note": str(e)[:90]}
# K3: the long-prompt band (~30k chars)
try:
    long_diff = ("ctx-line about the loader's validation\n" * 1200) + \
        "REAL-CHANGE: the load() raises FileNotFoundError"
    t0 = time.time()
    d = post({"model": M, "messages": [{"role": "user", "content":
              f'In this context-find the REAL-CHANGE line and reply ONLY '
              f'JSON {{"found": true, "line": "it"}}.\n' + long_diff}],
              "max_tokens": 60})
    c = content(d)
    K["k3_long"] = {"ok": '"found"' in c and "REAL-CHANGE" in c,
                    "prompt_chars": len(long_diff),
                    "latency_s": round(time.time() - t0, 2), "note": c[:90]}
except Exception as e:
    K["k3_long"] = {"ok": False, "note": str(e)[:90]}


# K4: the threaded 5-parallel
def one(i):
    t0 = time.time()
    post({"model": M, "messages": [{"role": "user", "content":
          f'Reply ONLY JSON: {{"n": {i}}}.'}], "max_tokens": 30})
    return round(time.time() - t0, 2)


try:
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=5) as ex:
        lats = list(ex.map(one, range(5)))
    K["k4_threaded"] = {"ok": len(lats) == 5, "wall_s":
                        round(time.time() - t0, 2),
                        "sum_latencies": sum(lats), "lats": lats,
                        "note": f"the wall {round(time.time() - t0, 2)}s vs "
                                f"the serial {round(sum(lats), 1)}s"}
except Exception as e:
    K["k4_threaded"] = {"ok": False, "note": str(e)[:90]}

with open(os.path.join(ROOT, "Config", "groq_120b_knobs.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "knobs": K,
               "cost": "$0.00", "verdict": "the wiring follows the winners"},
              f, ensure_ascii=False, indent=1)
for k, v in K.items():
    print(f"[knob] {k}: ok={v['ok']} | {v['note'][:80]}")