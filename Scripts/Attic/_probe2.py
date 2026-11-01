"""FREE-MODEL PROBE #2 (the fixes): gemini's ?key= on the generate-URL;
github-models' real endpoint variants; groq's CloudBrain-mimic call;
openrouter = the honest day-cap (not re-probed)."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from CloudBrain import env_keys

ASK = ('Reply ONLY the JSON {"ship": true, "why": "the patch is scoped"} '
       "for a one-line docstring fix.")
P = {}


def post(url, body, headers, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def gemini(k):
    try:
        r = post("https://generativelanguage.googleapis.com/v1beta/models/"
                 "gemini-2.5-flash:generateContent?key=" + k,
                 {"contents": [{"parts": [{"text": ASK}]}]},
                 {"Content-Type": "application/json"})
        out = (r.get("candidates") or [{}])[0].get("content", {}).get(
            "parts", [{}])[0].get("text", "")
        P["gemini"] = {"ok": '"ship"' in out, "note":
                       f"gemini-2.5-flash -> {len(out)} chars, "
                       f"usage-keys: {list((r.get('usageMetadata') or {}).keys())[:3]}"}
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        P["gemini"] = {"ok": False,
                       "note": f"{e.__class__.__name__} {(body or b'')[:140]}"}


def github_models(tok):
    ids = ("openai/gpt-4o-mini", "openai/gpt-4.1-mini", "github/gpt-4o-mini")
    for mid in ids:
        try:
            r = post("https://models.github.ai/inference/chat/completions",
                     {"model": mid, "messages": [{"role": "user",
                                                  "content": ASK}]},
                     {"Authorization": "Bearer " + tok, "Content-Type":
                      "application/json"})
            out = (r.get("choices") or [{}])[0].get("message", {}).get(
                "content", "")
            P["github_models"] = {"ok": '"ship"' in out,
                                  "model": mid, "note": f"{len(out)} chars"}
            return
        except Exception as e:
            body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
            last = f"{mid}: {e.__class__.__name__} {(body or b'')[:100]}"
    P["github_models"] = {"ok": False, "note": last}


def groq(k):
    try:
        r = post("https://api.groq.com/openai/v1/chat/completions",
                 {"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": ASK}]},
                 {"Authorization": "Bearer " + k, "Content-Type":
                  "application/json", "User-Agent":
                  "apex-free-tier/1.0 (+github.com/seahawk2986-hue)"},
                 timeout=30)
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        P["groq"] = {"ok": '"ship"' in out,
                     "note": f"llama-3.3-70b-versatile -> {len(out)} chars"}
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        P["groq"] = {"ok": False,
                     "note": f"{e.__class__.__name__} {(body or b'')[:140]}"}


keys = env_keys()
try:
    import PatchStep as PS
    tok = PS.token()
except Exception:
    tok = ""
if keys.get("GEMINI_API_KEY"):
    gemini(keys["GEMINI_API_KEY"])
if tok:
    github_models(tok)
if keys.get("GROQ_API_KEY"):
    groq(keys["GROQ_API_KEY"])
P["openrouter"] = {"ok": False, "note": "the day's free-quota spent "
                   "(rate-limited $0 tier) - the cooldown lane retries "
                   "after the reset; NO credits added (the $0.00 law)"}
with open(os.path.join(ROOT, "Config", "free_model_probe.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "round": 2,
               "probes": P, "law": "every lane $0.00-verified"},
              f, ensure_ascii=False, indent=1)
print("[probe2] " + json.dumps({k: v["ok"] for k, v in P.items()}))
for k, v in P.items():
    print(f"  {k}: {v['note'][:110]}")