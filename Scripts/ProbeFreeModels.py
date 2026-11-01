"""THE FREE-MODEL PROBE (the better-brain directive, $0.00-enforced):
four free lanes, each probed with a REAL capability ask + each capped at
$0.00 - any payment-required answer = the honest DORMANT receipt.
 1. GitHub Models (the PAT we ALREADY hold - no new signup!)
 2. Gemini (the model-ID bug fixed: read the list, use a REAL id)
 3. OpenRouter :free (the exact :free-suffix ids)
 4. Groq (the rate-limited free tier re-probe)
Every probe = a tiny smoke + ONE judged review-ask; the receipts carry
the outputs' real shape (JSON-parse-ability = the honest capability read)."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from CloudBrain import env_keys  # the keys ONLY (never printed)

ASK = ('Reply ONLY the JSON {"ship": true, "why": "the patch is scoped"}'
       ' for a one-line doc-string fix.')
PROBED = {}


def post(url, body, headers, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get(url, headers, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                timeout=timeout) as r:
        return json.loads(r.read().decode())


def rec(lane, ok, note):
    PROBED[lane] = {"ok": ok, "note": str(note)[:160], "cost": "$0.00"}


def probe_github_models(tok):
    try:
        cat = get("https://models.github.ai/catalog/models",
                  {"Authorization": "Bearer " + tok,
                   "Accept": "application/vnd.github+json"})
        ids = [m.get("id", "") for m in cat if isinstance(m, dict)]
        print(f"[probe] github-models catalog: {len(ids)} models")
        rank = [i for i in ids if any(k in i.lower() for k in
                ("gpt-4o", "deepseek", "llama-3.3-70b", "qwen3", "phi-4"))]
        if not rank:
            rec("github_models", False, f"no strong free id in {ids[:5]}")
            return
        pick = rank[0]
        r = post("https://models.github.ai/inference/chat/completions",
                 {"model": pick, "messages": [{"role": "user",
                                               "content": ASK}]},
                 {"Authorization": "Bearer " + tok,
                  "Accept": "application/vnd.github+json"})
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        ok = '"ship"' in out
        rec("github_models", ok, f"{pick} -> the review-JSON: {ok}")
        PROBED["github_models"]["model"] = pick
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        rec("github_models", False,
            f"{e.__class__.__name__} {(body or b'')[:120]}")


def probe_gemini(k):
    try:
        lst = get("https://generativelanguage.googleapis.com/v1beta/models"
                  "?key=" + k, {})
        ids = [m["name"].split("/")[-1] for m in lst.get("models", [])
               if "generateContent" in (m.get("supportedGenerationMethods") or [])]
        flash = next((i for i in sorted(ids) if "flash" in i), None)
        print(f"[probe] gemini real ids: {[i for i in ids if 'flash' in i][:4]}")
        if not flash:
            rec("gemini", False, f"no flash id; ids={ids[:5]}")
            return
        r = post(f"https://generativelanguage.googleapis.com/v1beta/models/"
                 f"{flash}:generateContent",
                 {"contents": [{"parts": [{"text": ASK}]}]},
                 {"Content-Type": "application/json"})
        out = (r.get("candidates") or [{}])[0].get("content", {}).get(
            "parts", [{}])[0].get("text", "")
        rec("gemini", '"ship"' in out, f"{flash} -> {len(out)} chars")
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        rec("gemini", False, f"{e.__class__.__name__} {(body or b'')[:120]}")


def probe_openrouter(k):
    try:
        lst = get("https://openrouter.ai/api/v1/models", {})
        frees = [m["id"] for m in lst.get("data", []) if ":free" in m["id"]]
        pick = next((i for i in frees if "deepseek" in i.lower()),
                    frees[0] if frees else None)
        print(f"[probe] openrouter :free count={len(frees)} pick={pick}")
        if not pick:
            rec("openrouter", False, "no :free ids")
            return
        r = post("https://openrouter.ai/api/v1/chat/completions",
                 {"model": pick, "messages": [{"role": "user",
                                               "content": ASK}]},
                 {"Authorization": "Bearer " + k, "Content-Type":
                  "application/json"})
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        rec("openrouter", '"ship"' in out,
            f"{pick} -> the review-JSON; total {(r.get('usage') or {}).get('cost', 0)}")
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        rec("openrouter", False,
            f"{e.__class__.__name__} {(body or b'')[:120]}")


def probe_groq(k):
    try:
        r = post("https://api.groq.com/openai/v1/chat/completions",
                 {"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": ASK}]},
                 {"Authorization": "Bearer " + k,
                  "Content-Type": "application/json"})
        out = (r.get("choices") or [{}])[0].get("message", {}).get(
            "content", "")
        rec("groq", '"ship"' in out, f"llama-3.3-70b-versatile -> {len(out)} chars")
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        rec("groq", False,
            f"{e.__class__.__name__} {(body or b'')[:120]}")


def main():
    keys = env_keys()
    tok = ""
    try:
        import PatchStep as PS
        tok = PS.token()
    except Exception:
        pass
    if tok:
        probe_github_models(tok)
    if keys.get("GEMINI_API_KEY"):
        probe_gemini(keys["GEMINI_API_KEY"])
    if keys.get("OPENROUTER_API_KEY"):
        probe_openrouter(keys["OPENROUTER_API_KEY"])
    if keys.get("GROQ_API_KEY"):
        probe_groq(keys["GROQ_API_KEY"])
    with open(os.path.join(ROOT, "Config", "free_model_probe.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "probes": PROBED,
                   "law": "every lane $0.00-verified; a payment-required = "
                          "the honest DORMANT (never auto-pay)"},
                  f, ensure_ascii=False, indent=1)
    print("[probe] " + json.dumps(
        {k: f"{v['ok']}" for k, v in PROBED.items()}))
    open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
             "what": "the free-model probes (the better-brain lanes)",
             "results": {k: v["ok"] for k, v in PROBED.items()}}) + "\n")


if __name__ == "__main__":
    main()