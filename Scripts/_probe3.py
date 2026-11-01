"""FREE-MODEL PROBE #3: the LIST-driven ids (the honest upgrade of the
lesson: never trust a hardcoded model-id - the LISTS are the truth).
gemini: gemini-flash-latest (the alias). groq: the /models live-list pick.
github-models: the /inference/models list-try."""
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
H_JSON = {"Content-Type": "application/json", "User-Agent":
          "apex-free-tier/1.0 (+github.com/seahawk2986-hue)"}


def post(url, body, headers, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get(url, headers, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                timeout=timeout) as r:
        return json.loads(r.read().decode())


def gemini(k):
    try:
        r = post("https://generativelanguage.googleapis.com/v1beta/models/"
                 "gemini-flash-latest:generateContent?key=" + k,
                 {"contents": [{"parts": [{"text": ASK}]}]},
                 {"Content-Type": "application/json"})
        out = (r.get("candidates") or [{}])[0].get("content", {}).get(
            "parts", [{}])[0].get("text", "")
        um = r.get("usageMetadata") or {}
        P["gemini"] = {"ok": '"ship"' in out, "model":
                       "gemini-flash-latest", "note":
                       f"{len(out)} chars; usage-keys {list(um)[:4]}"}
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        P["gemini"] = {"ok": False,
                       "note": f"{e.__class__.__name__} {(body or b'')[:140]}"}


def groq(k):
    try:
        lst = get("https://api.groq.com/openai/v1/models",
                  {"Authorization": "Bearer " + k, **H_JSON})
        ids = [m["id"] for m in lst.get("data", []) if "whisper" not in
               m["id"] and "guard" not in m["id"] and "tts" not in m["id"]]
        pick = next((i for i in ids if "70b" in i or "120b" in i),
                    ids[0] if ids else None)
        print(f"[probe3] groq live ids: {ids[:6]} pick={pick}")
        if not pick:
            P["groq"] = {"ok": False, "note": f"ids={ids}"}
            return
        r = post("https://api.groq.com/openai/v1/chat/completions",
                 {"model": pick, "messages": [{"role": "user",
                                               "content": ASK}]},
                 {"Authorization": "Bearer " + k, **H_JSON}, timeout=30)
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        u = (r.get("x_groq") or {})
        P["groq"] = {"ok": '"ship"' in out, "model": pick,
                     "note": f"{len(out)} chars (the review-JSON: "
                             f"{'LIVE' if '\"ship\"' in out else 'shape-off'})"}
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        P["groq"] = {"ok": False,
                     "note": f"{e.__class__.__name__} {(body or b'')[:140]}"}


def github(tok):
    try:
        lst = get("https://models.github.ai/inference/models",
                  {"Authorization": "Bearer " + tok,
                   "Accept": "application/vnd.github+json"})
        ids = [m.get("id") or m.get("name") for m in lst] if isinstance(
            lst, list) else []
        print(f"[probe3] github-models ids: {ids[:6]}")
        pick = next((i for i in ids if "4.1-mini" in i or "4o-mini" in i),
                    ids[0] if ids else None)
        if not pick:
            P["github_models"] = {"ok": False, "note": f"ids={ids}"}
            return
        r = post("https://models.github.ai/inference/chat/completions",
                 {"model": pick, "messages": [{"role": "user",
                                               "content": ASK}]},
                 {"Authorization": "Bearer " + tok, **H_JSON}, timeout=40)
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        P["github_models"] = {"ok": '"ship"' in out, "model": pick,
                              "note": f"{len(out)} chars"}
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        P["github_models"] = {"ok": False,
                              "note": f"{e.__class__.__name__} "
                                      f"{(body or b'')[:140]}"}


keys = env_keys()
try:
    import PatchStep as PS
    tok = PS.token()
except Exception:
    tok = ""
if keys.get("GEMINI_API_KEY"):
    gemini(keys["GEMINI_API_KEY"])
if keys.get("GROQ_API_KEY"):
    groq(keys["GROQ_API_KEY"])
if tok:
    github(tok)
with open(os.path.join(ROOT, "Config", "free_model_probe.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "round": 3,
               "probes": P, "law": "the LIST-driven ids; $0.00 enforced"},
              f, ensure_ascii=False, indent=1)
print("[probe3] " + json.dumps({k: v["ok"] for k, v in P.items()}))
for k, v in P.items():
    print(f"  {k}: {v['note'][:120]}")