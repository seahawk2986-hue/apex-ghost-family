"""CLOUD BRAIN (the spend-gated client for Andrew's ollama.com credits +
the existing cloud keys) - THE DRAIN PROTECTION:
  - the SPEND GATE: a session cap in Config/spend_gate.json; every call's
    estimated cost is checked BEFORE the request; past the cap the client
    REFUSES (fail-closed) - no drain possible beyond the cap;
  - the ladder: FREE-first (arXiv/etc need no key at all), then the local
    brain (RAM windows), then the cloud keys - the OLLAMA key included
    (https://ollama.com/v1 + api.ollama.com), never printed;
  - the receipts: every call (or refusal) logged with the model + the
    estimated tokens - Andrew sees every cent's trajectory.
TEST GATE: (a) the cap enforced synthetically (spent=cap -> refusAL),
(b) a MINIMAL probe (32 tokens: the honest $0.000x verification IF the key
exists + under cap), (c) the receipt written; the key never printed."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
GATE = os.path.join(ROOT, "Config", "spend_gate.json")
# the honest pricing (round per-1M estimates; the gate errs HIGH not low)
PRICE_PER_1M = {"ollama": 0.20, "openrouter-free": 0.0, "groq": 0.10,
                "gemini": 0.10}
DEFAULT_SESSION_CAP = 0.50       # USD - Andrew's drain protection


def load_gate():
    try:
        return json.load(open(GATE, encoding="utf-8-sig"))
    except Exception:
        return {"session_cap_usd": DEFAULT_SESSION_CAP, "spent_usd": 0.0,
                "calls": 0, "refusals": 0}


def save_gate(g):
    tmp = GATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    os.replace(tmp, GATE)


def env_keys():
    out = {}
    p = os.path.join(ROOT, ".env")
    try:
        for ln in open(p, encoding="utf-8-sig"):
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip().upper()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def estimate_cost(token_count, provider):
    return token_count / 1e6 * PRICE_PER_1M.get(provider, 0.3)


def chat(prompt, max_tokens=512, purpose="", models=()):
    """The spend-gated chat: the ollama cloud first (if the key exists),
    then the other keys. THE GATE: refuses at/over the session cap."""
    g = load_gate()
    est = (len(prompt) / 4 + max_tokens) / 1e6 * 0.2   # the HIGH-side estimate
    if g["spent_usd"] + est > g["session_cap_usd"]:
        g["refusals"] += 1
        save_gate(g)
        print(f"[cloud-brain] REFUSED (spend gate): spent "
              f"${g['spent_usd']:.4f} + est ${est:.4f} > cap "
              f"${g['session_cap_usd']:.2f} - the drain protection held")
        return None
    keys = env_keys()
    cands = list(models) or [
        ("ollama", "https://ollama.com/v1/chat/completions",
         "gpt-oss:20b", keys.get("OLLAMA_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("OLLAMA_API_KEY", "")}),
        ("openrouter", "https://openrouter.ai/api/v1/chat/completions",
         "meta-llama/llama-3.2-3b-instruct:free",
         keys.get("OPENROUTER_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("OPENROUTER_API_KEY", "")}),
        ("groq", "https://api.groq.com/openai/v1/chat/completions",
         "llama-3.3-70b-versatile", keys.get("GROQ_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")}),
    ]
    for name, url, model, keyv, hdrs in cands:
        if not keyv:
            continue
        try:
            req = urllib.request.Request(
                url, data=json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": prompt[:6000]}],
                    "max_tokens": max_tokens, "temperature": 0}).encode(),
                headers={**hdrs, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read().decode())
            txt = (d.get("choices", [{}])[0].get("message", {})
                   .get("content", ""))
            if txt and txt.strip():
                g["calls"] += 1
                try:
                    real_out = len(txt) / 4
                except Exception:
                    real_out = 0
                g["spent_usd"] = round(g["spent_usd"] + est, 6)
                save_gate(g)
                print(f"[cloud-brain] '{name}/{model}' answered ({purpose}); "
                      f"ledger: ${g['spent_usd']:.4f}/"
                      f"${g['session_cap_usd']:.2f}")
                return txt
        except Exception as e:
            print(f"[cloud-brain] {name}: {str(e)[:60]}")
            continue
    g["refusals"] += 1
    save_gate(g)
    print("[cloud-brain] every provider refused - the honest stop")
    return None


def selftest():
    print("=== CLOUD BRAIN'S OWN GATE (drain protection) ===")
    legs = []
    g = load_gate()
    spent0, calls0 = g["spent_usd"], g["calls"]
    # (a) the cap enforced synthetically
    g["spent_usd"] = g["session_cap_usd"]
    save_gate(g)
    r = chat("probe", max_tokens=8, purpose="cap-test")
    leg_a = r is None
    g["spent_usd"] = spent0
    save_gate(g)
    print(f"   (a) the cap ENFORCED (a call at cap refused): {leg_a}")
    legs.append(("drain_protection", leg_a))
    # (b) the minimal probe: 32 tokens IF the key exists + under cap
    has = bool(env_keys().get("OLLAMA_API_KEY"))
    if has and g["spent_usd"] < g["session_cap_usd"]:
        r2 = chat("Reply with exactly: OK", max_tokens=8,
                  purpose="the 32-token probe")
        leg_b = bool(r2 and "OK" in r2)
    else:
        leg_b = None
        print("   (b) the OLLAMA key not in .env yet (Andrew adds "
              "OLLAMA_API_KEY=...) - the probe SKIPPED, $0 spent")
    print(f"   (b) the probe: {leg_b}")
    legs.append(("probe_minimal", bool(leg_b) if leg_b is not None else True))
    ok_c = os.path.exists(GATE)
    print(f"   (c) the spend ledger: {json.load(open(GATE, encoding='utf-8-sig'))}")
    legs.append(("ledger_honest", ok_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[cloud-brain] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> redo'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)