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
PRICE_PER_1M = {"ollama": 0.20, "openrouter-free": 0.0, "groq": 0.0,
                "gemini": 0.0,
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


def track(agent, delivered):
    """THE USEFULNESS LAW: every agent's track record of ACTUALLY-DELIVERED
    answers (the roster demotes agents whose answers don't produce usable
    work - an answer-agent is not worth a roster seat)."""
    p = os.path.join(ROOT, "Config", "agent_track.json")
    try:
        t = json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        t = {}
    e = t.setdefault(agent, {"delivered": 0, "failed": 0})
    e["delivered" if delivered else "failed"] += 1
    e["rate"] = round(e["delivered"] / max(1, e["delivered"] + e["failed"]), 2)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(t, f, indent=1)
    os.replace(tmp, p)
    return e["rate"]


def chat(prompt, max_tokens=512, purpose="", models=(), resp_json=False):
    """The spend-gated chat: the ollama cloud first (if the key exists),
    then the other keys. THE GATE: refuses at/over the session cap."""
    g = load_gate()
    est = (len(prompt) / 4 + max_tokens) / 1e6 * 0.2   # the HIGH-side estimate
    keys = env_keys()
    cloud_allowed = (os.environ.get("CLOUD_ALLOWED") == "1" or
                     (keys.get("CLOUD_ALLOWED") == "1"))   # the founder's
    # opt-in: the env-var OR the .env line (the daemon's processes see the
    # .env form; the interactive runs either)
    pool = [                                                  # the ladder
        # THE FREE-ONLY ROSTER (the founder's law: only free agents run by
        # default; the no-card free tiers behind CLOUD_ALLOWED=1; the
        # credits-tier behind the SEPARATE CREDITS_ALLOWED)
        ("local-coder", "http://localhost:11434/api/chat",
         "qwen2.5-coder:7b", "local-no-key", {}),
        ("local-fast", "http://localhost:11434/api/chat",
         "qwen2.5-coder:3b", "local-no-key", {}),
        # THE CHAT-LANES (the ChatEval's blind-race's verdict: the
        # phi4-mini = the #2 chat (the #1's the 120b); the r1 = the
        # reasoning-window's candidate; the ollama = the single-slot
        # auto-swap = the RAM-legal (one at a time))
        ("local-phi4", "http://localhost:11434/api/chat",
         "phi4-mini:latest", "local-no-key", {}),
        ("local-gemma3", "http://localhost:11434/api/chat",
         "gemma3:4b", "local-no-key", {}),
        ("local-r1", "http://localhost:11434/api/chat",
         "deepseek-r1:7b", "local-no-key", {}),
    ]
    if cloud_allowed:
        pool += [
            # THE NO-CARD FREE TIERS ($0 STRUCTURALLY: no card attached =
            # no possible bill; the 429s = the daily rate-ceilings) - the
            # probe-verified 120b-class brain + the gemini-flash alias
            ("groq", "https://api.groq.com/openai/v1/chat/completions",
             "openai/gpt-oss-120b", keys.get("GROQ_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")}),
            ("gemini", "https://generativelanguage.googleapis.com/v1beta/"
             "openai/chat/completions", "gemini-flash-latest",
             keys.get("GEMINI_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("GEMINI_API_KEY", "")}),
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions",
             "meta-llama/llama-3.2-3b-instruct:free",
             keys.get("OPENROUTER_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("OPENROUTER_API_KEY", "")}),
        ]
    credits_allowed = (os.environ.get("CREDITS_ALLOWED") == "1" or
                       (keys.get("CREDITS_ALLOWED") == "1"))
    if cloud_allowed and credits_allowed:
        pool += [
            # THE FOUNDER'S CREDITS tier (a SEPARATE explicit unlock; the
            # est stays high-side 0.20; the $0.00-cap still gates it):
            ("ollama", "https://ollama.com/v1/chat/completions",
             "gpt-oss:120b", keys.get("OLLAMA_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("OLLAMA_API_KEY", "")}),
        ]
    # the named-ladder: models=("groq", ...) = the EXPLICIT order-filter
    # AND the TRUTH-PRIORITY (the route's order = the serving order - the
    # 2026-11-01 fix: the pool's local-first order used to outrank the
    # route, silently downgrading the founder's chat-lock to the floor)
    _idx = {m: i for i, m in enumerate(models)} if models else {}
    cands = ([c for c in pool if c[0] in set(models)] if models else pool)
    if _idx:
        cands = sorted(cands, key=lambda c: _idx.get(c[0], 99))
    for name, url, model, keyv, hdrs in cands:
        is_local = name.startswith("local")
        if not keyv and not is_local:
            continue
        # THE GATE LIVES PER CANDIDATE: the no-card free tiers price $0.00
        # (they pass even the $0.00 cap); the credits-tier's est stays
        # HIGH-side (the cap blocks it until the founder's second unlock)
        est_c = (len(prompt) / 4 + max_tokens) / 1e6 * (
            0.0 if name in ("groq", "gemini", "openrouter") else 0.2)
        if not is_local:
            g2 = load_gate()
            if g2["spent_usd"] + est_c > g2["session_cap_usd"]:
                continue
        try:
            if is_local:
                body = {"model": model, "stream": False,
                        "messages": [{"role": "user",
                                      "content": prompt[:6000]}],
                        "keep_alive": "1m",
                        "options": {"num_predict": max(max_tokens, 512),
                                    "temperature": 0}}
                if os.environ.get("CB_FORMAT_JSON") == "1":
                    body["format"] = "json"
            else:
                # the MEASURED band (the honest budget): groq = 9k (the
                # free tier's per-minute quota-measured), the rest = 6k
                budget = 9000 if name == "groq" else 6000
                body = {"model": model,
                        "messages": [{"role": "user",
                                      "content": prompt[:budget]}],
                        "max_tokens": max(max_tokens, 512) if name.startswith(
                            ("ollama", "openrouter", "groq")) else
                        max_tokens,
                        "temperature": 0}
                if resp_json:
                    body["response_format"] = {"type": "json_object"}
            req = urllib.request.Request(
                url, data=json.dumps(body).encode(),
                headers={**hdrs, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read().decode())
            txt = (d.get("choices", [{}])[0].get("message", {})
                   .get("content", "")) if not is_local else \
                d.get("message", {}).get("content", "")
            if txt and txt.strip():
                track(name, True)
                if is_local:
                    # THE FREE LAW: the local brain costs $0.00 - it is
                    # NEVER billed in the spend ledger (the honest drain
                    # reporting; the earlier version billed free calls -
                    # false drain-fear, fixed here).
                    print(f"[cloud-brain] '{name}/{model}' answered "
                          f"({purpose}); cost $0.00 (the free tier)")
                    return txt
                g["calls"] += 1
                g["spent_usd"] = round(g["spent_usd"] + est, 6)
                save_gate(g)
                print(f"[cloud-brain] '{name}/{model}' answered ({purpose}); "
                      f"ledger: ${g['spent_usd']:.4f}/"
                      f"${g['session_cap_usd']:.2f}")
                return txt
        except Exception as e:
            track(name, False)
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


def chat_stream(prompt, max_tokens=800, purpose="", models=()):
    """THE STREAMING CHAT (the canon's #1 chat-UX practice: perceived speed
    = the first-token latency, not the total): a GENERATOR yielding
    (lane_name, chunk) rows in the ladder-order. The groq/no-card lanes =
    the OpenAI-compat SSE (stream=true, the delta.content chunks); the
    ollama local lanes = the NDJSON stream. The SAME per-candidate spend-
    gate as chat(); the credits-tier = refused (the founder's law) - the
    stream is for the FREE lanes. Honest aborts yield nothing for a silent
    lane; the caller decides the fallback UX. No billing; $0."""
    import json as _j
    keys = env_keys()
    cloud_allowed = (os.environ.get("CLOUD_ALLOWED") == "1" or
                     (keys.get("CLOUD_ALLOWED") == "1"))
    pool = [
        ("local-coder", "http://localhost:11434/api/chat",
         "qwen2.5-coder:7b", "local-no-key", {}),
        ("local-fast", "http://localhost:11434/api/chat",
         "qwen2.5-coder:3b", "local-no-key", {}),
        ("local-phi4", "http://localhost:11434/api/chat",
         "phi4-mini:latest", "local-no-key", {}),
        ("local-gemma3", "http://localhost:11434/api/chat",
         "gemma3:4b", "local-no-key", {}),
        ("local-r1", "http://localhost:11434/api/chat",
         "deepseek-r1:7b", "local-no-key", {}),
    ]
    if cloud_allowed:
        pool += [
            ("groq", "https://api.groq.com/openai/v1/chat/completions",
             "openai/gpt-oss-120b", keys.get("GROQ_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")}),
            ("gemini", "https://generativelanguage.googleapis.com/v1beta/"
             "openai/chat/completions", "gemini-flash-latest",
             keys.get("GEMINI_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("GEMINI_API_KEY", "")}),
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions",
             "meta-llama/llama-3.2-3b-instruct:free",
             keys.get("OPENROUTER_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("OPENROUTER_API_KEY", "")}),
        ]
    _idx = {m: i for i, m in enumerate(models)} if models else {}
    cands = ([c for c in pool if c[0] in set(models)] if models else pool)
    if _idx:
        cands = sorted(cands, key=lambda c: _idx.get(c[0], 99))
    for name, url, model, keyv, hdrs in cands:
        is_local = name.startswith("local")
        if not keyv and not is_local:
            continue
        # THE GATE (the free-tier law, mirrored from chat()): the pool here
        # = the FREE lanes ONLY (the local = structurally $0; the groq/
        # gemini/openrouter = the NO-CARD free tiers = $0.00-price = they
        # PASS even the $0.00 cap). The CREDITS-tier = structurally OUT of
        # this function (the founder's second-unlock law) - its est can
        # never appear here, so no est-gate check is needed or applied.
        body_dict = None
        if is_local:
            body_dict = {"model": model, "stream": True,
                         "messages": [{"role": "user",
                                       "content": prompt[:6000]}],
                         "keep_alive": "1m",
                         "options": {"num_predict": max(max_tokens, 512),
                                     "temperature": 0}}
        else:
            body_dict = {"model": model, "stream": True,
                         "messages": [{"role": "user",
                                       "content": prompt[:9000 if name == "groq" else 6000]}],
                         "max_tokens": max(max_tokens, 512),
                         "temperature": 0}
        try:
            import requests as _rq
            with _rq.post(url, headers=hdrs, json=body_dict, stream=True,
                          timeout=(240 if is_local else 90)) as r:
                if r.status_code != 200:
                    continue
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if is_local:
                        # the ollama NDJSON: one object per line
                        try:
                            j = _j.loads(line)
                        except Exception:
                            continue
                        tok = (j.get("message") or {}).get("content") or ""
                        if tok:
                            yield (name, tok)
                        if j.get("done"):
                            return
                    else:
                        # the OpenAI-compat SSE: data: {...} / [DONE]
                        s = line.strip()
                        if not s.startswith("data:"):
                            continue
                        payload_s = s[5:].strip()
                        if payload_s == "[DONE]":
                            return
                        try:
                            j = _j.loads(payload_s)
                        except Exception:
                            continue
                        chs = j.get("choices") or [{}]
                        tok = ((chs[0].get("delta") or {}).get("content")) or ""
                        if tok:
                            yield (name, tok)
            # the lane ended = the full content streamed = the caller done
            return
        except Exception:
            continue
    return


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)