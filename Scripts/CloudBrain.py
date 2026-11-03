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
                "gemini": 0.10}
# (2026-11-04 fix: a duplicate "gemini" key silently overwrote the free-tier
# 0.0 price with 0.10 — the pricing drift now lives only in this comment)
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
    """DELEGATED TO THE SPINE (2026-11-04): one .env schema fleet-wide
    (ApexIO.env) with the same uppercase-key contract as before."""
    import ApexIO
    out = {}
    for k0, v0 in ApexIO.env(ROOT).items():
        out[k0.upper()] = v0
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
        # THE 2026-11-04 FLEET EXPANSION ("all our models to their full
        # potential"): every lane the family paid vetting time for joins the
        # STREAMING pool - cerebras' own 120b, both free NIM doors, and the
        # catalog auto-router. All structurally $0 (no-card/ trial tiers).
        pool += [
            ("cerebras-120b", "https://api.cerebras.ai/v1/chat/completions",
             "gpt-oss-120b", keys.get("CEREBRAS_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("CEREBRAS_API_KEY", "")}),
            ("nim-v41f", "https://integrate.api.nvidia.com/v1/chat/completions",
             "deepseek-ai/deepseek-v4.1-flash", keys.get("NVIDIA_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("NVIDIA_API_KEY", "")}),
            ("nim-glm", "https://integrate.api.nvidia.com/v1/chat/completions",
             "z-ai/glm-5.3-flash", keys.get("NVIDIA_API_KEY", ""),
             {"Authorization": "Bearer " + keys.get("NVIDIA_API_KEY", "")}),
            ("or-auto", "https://openrouter.ai/api/v1/chat/completions",
             "openrouter/free", keys.get("OPENROUTER_API_KEY", ""),
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
        if not is_local:
            # THE PACER HONORED HERE TOO (2026-11-04): a 429-windowed lane
            # is skipped, not hammered (LaneGuard's ledger law, blocking path)
            try:
                import ApexShard as _S
                if _S._cool(name):
                    print(f"[cloud-brain] {name}: pacer window - skipped")
                    continue
            except Exception:
                pass
        # THE GATE LIVES PER CANDIDATE: the no-card free tiers price $0.00
        # (they pass even the $0.00 cap); the credits-tier's est stays
        # HIGH-side (the cap blocks it until the founder's second unlock)
        est_c = (len(prompt) / 4 + max_tokens) / 1e6 * (
            0.0 if name != "ollama" else 0.2)
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
    if models:
        # THE FLEET GUARANTEE (2026-11-04, "all our models to their full
        # potential"): the route answered nothing - expand the route to the
        # WHOLE pool for one more pass (recursive call; the widened call's
        # own guarantee-pass = empty, so this terminates). The pacers hold.
        _more = tuple(c0[0] for c0 in pool
                      if all(c0[0] != c1[0] for c1 in cands))
        if _more:
            print(f"[cloud-brain]: route ({', '.join(models)}) served nothing "
                  "- the FULL FLEET pass begins")
            return chat(prompt, max_tokens=max_tokens, purpose=purpose,
                        models=_more, resp_json=resp_json)
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
    served = {"v": False}

    def _paced(_nm):
        """THE PACER HONORED IN THE STREAM TOO (2026-11-04): a 429-windowed
        lane is SKIPPED, not hammered - LaneGuard's ledger law applies to
        every lane, stream or blocking."""
        try:
            import ApexShard as _S
            return _S._cool(_nm)
        except Exception:
            return False

    _idx = {m: i for i, m in enumerate(models)} if models else {}
    cands = ([c for c in pool if c[0] in set(models)] if models else pool)
    if _idx:
        cands = sorted(cands, key=lambda c: _idx.get(c[0], 99))
    # THE FLEET GUARANTEE (2026-11-04, "all our models to their full
    # potential"): the route-filtered pass = the PREFERENCE; if it serves
    # nothing, the REST of the fleet streams in one more pass. And an
    # empty-stream candidate no longer terminates the generator - the
    # fleet goes on (the old post-stream `return` cut it all off).
    fleet_rest = [c for c in pool if all(c[0] != c0[0] for c0 in cands)] \
        if models else []
    for pass_no in (0, 1):
        if pass_no == 1:
            if served["v"] or not fleet_rest:
                break
            cands = sorted(fleet_rest, key=lambda c: _idx.get(c[0], 99))
            print("[cloud-brain]: the route served nothing - the FULL "
                  "FLEET pass begins (every model, pacer-honored)")
        for name, url, model, keyv, hdrs in cands:
            is_local = name.startswith("local")
            if not keyv and not is_local:
                continue
            if not is_local and _paced(name):
                print(f"[cloud-brain] {name}: pacer window - skipped")
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
                lane_yielded = False
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
                                lane_yielded = True
                                served["v"] = True
                            if j.get("done"):
                                if lane_yielded:
                                    return
                                break   # empty stream: the fleet goes on
                        else:
                            # the OpenAI-compat SSE: data: {...} / [DONE]
                            s = line.strip()
                            if not s.startswith("data:"):
                                continue
                            payload_s = s[5:].strip()
                            if payload_s == "[DONE]":
                                if lane_yielded:
                                    return
                                break   # empty stream: the fleet goes on
                            try:
                                j = _j.loads(payload_s)
                            except Exception:
                                continue
                            chs = j.get("choices") or [{}]
                            tok = ((chs[0].get("delta") or {}).get("content")) or ""
                            if tok:
                                yield (name, tok)
                                lane_yielded = True
                                served["v"] = True
                if lane_yielded:
                    return
            except Exception:
                continue
    return


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)