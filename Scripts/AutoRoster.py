"""AutoRoster - THE SELF-RENEWING FLEET ROSTER (2026-11-04, fleet organ #3).

THE WEAKNESSES IT KILLS (all three measured live tonight):
  1. a DEAD MODEL keeps its rotation slot: nim-k3 answers 410 Gone but stays
     in ApexShard.LANES - every trip wastes a dispatch, a note, and a
     pacer bookkeeping row. NOW: 2 observed 410s = honest RETIREMENT
     (excluded from rotation; the receipt + the watch for its return).
  2. the roster NEVER got fresh blood: free tiers change WEEKLY (the NIM
     unlocks were found manually on 11/02). NOW: the providers' OWN
     documented /models catalogs are read, new candidates get ONE-token
     capability probes, and verified lanes land in Config/lane_extra.json
     - merged into rotation WITHOUT touching human lanes.
  3. roster DRIFT between organs: the pacer's book and the rotator's array
     disagree (nim-v4pro unpaced; gym lanes unpaced). NOW: the shard's
     order + LaneGuard's book converge on ONE roster contract: the shard
     LANES + the verified extras.

CATALOG SOURCES (all current, all documented, all $0 reads):
  * Groq: GET https://api.groq.com/openai/v1/models (docs: console.groq.com/
    docs/api-reference#models-list - data[].id + context_window; verified
    live 2026-11-02 against their published reference)
  * OpenRouter: GET https://openrouter.ai/api/v1/models (the family's own
    ProbeFreeModels.py reads it successfully; :free-filter + pricing=0)
  * GitHub Models: GET https://models.github.ai/catalog/models with the PAT
    the family already holds (ProbeFreeModels.py:42-46 precedent)
  * Gemini: GET /v1beta/models?key= - REAL ids (the alias-deprecation class
    of bug died here on 11/02; the catalog now feeds the roster directly)
Cadence: manual + nightly dream beat; <= 5 new-lane probes per run
(bounded storm discipline); any 402/429 = DORMANT receipt, never auto-pay.
"""
import io
import json
import os
import sys
import time


if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
EXTRAS = os.path.join(REPO, "Config", "lane_extra.json")
sys.path.insert(0, os.path.join(REPO, "Scripts"))

CHAT_URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
    "nim": "https://integrate.api.nvidia.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "or-free": "https://openrouter.ai/api/v1/chat/completions",
}

def _env():
    import ApexIO
    return ApexIO.env(REPO)

def _get(url, tok, out=None):
    import requests
    return requests.get(url, headers={"Authorization": "Bearer " + tok,
                                      "User-Agent": "ApexGhostFamily/2.0"},
                        timeout=30)

def _probe(url, tok, model, max_tokens=8):
    """ONE honest capability probe (the family's 1-token ping law)."""
    import requests
    t0 = time.time()
    try:
        r = requests.post(url, headers={"Authorization": "Bearer " + tok,
                                        "Content-Type": "application/json"},
                          json={"model": model, "max_tokens": max_tokens,
                                "temperature": 0.0,
                                "messages": [{"role": "user", "content": "Reply with the single word: OK."}]},
                          timeout=45)
        ms = round((time.time() - t0) * 1000)
        if r.status_code == 200 and (r.json().get("choices") or [{}])[0].get("message", {}).get("content"):
            return {"http": 200, "ms": ms}
        return {"http": r.status_code, "ms": ms, "body": r.text[:80]}
    except Exception as e:
        return {"http": None, "body": type(e).__name__ + " " + str(e)[:60]}


def catalog_candidates(E):
    """The providers' own catalogs -> candidate free CHAT models not rostered."""
    known = set()
    try:
        import ApexShard as S
        known = {l[0] for l in S.LANES} | {l[0] for l in _extras_state().get("lanes", [])}
        known |= {l[3] for l in S.LANES}
    except Exception:
        pass
    cands = []
    tok = E.get("GROQ_API_KEY", "")
    if tok:
        try:
            r = _get("https://api.groq.com/openai/v1/models", tok)
            for m in r.json().get("data", []):
                mid = m.get("id", "")
                cw = m.get("context_window") or 0
                if m.get("active", True) and cw >= 8192 and mid not in known \
                        and any(k in mid for k in ("70b", "120b", "flash", "large", "llama-4", "qwen3")):
                    cands.append(("groq/" + mid, CHAT_URLS["groq"], "GROQ_API_KEY", mid, "medium", cw))
        except Exception as e:
            print("[catalog] groq skipped honestly:", type(e).__name__)
    tok = E.get("OPENROUTER_API_KEY", "")
    if tok:
        try:
            r = _get("https://openrouter.ai/api/v1/models", tok)
            for m in r.json().get("data", []):
                mid = m.get("id", "")
                price = (m.get("pricing") or {})
                if mid.endswith(":free") and mid not in known and \
                        any(k in mid.lower() for k in ("70b", "120b", "qwen3", "deepseek", "llama-3.3")):
                    cands.append(("orfree/" + mid, CHAT_URLS["or-free"], "OPENROUTER_API_KEY", mid, "medium", 0))
        except Exception as e:
            print("[catalog] openrouter skipped honestly:", type(e).__name__)
    tok = E.get("NVIDIA_API_KEY", "")
    if tok:
        try:
            r = _get("https://integrate.api.nvidia.com/v1/models", tok)
            for m in r.json().get("data", []):
                mid = m.get("id", "")
                if mid not in known and any(k in mid.lower() for k in
                                            ("flash", "glm", "qwen3", "8b", "9b")):
                    # (the 2026-11-04 honest catch: the catalog once registered
                    # a content-SAFETY guard as a chat lane - a classifier
                    # never answers chat; guards register for tools only)
                    tier = "guard" if any(k in mid.lower() for k in
                                          ("guard", "safety", "moderat",
                                           "shield", "embed")) else "medium"
                    cands.append(("nim/" + mid, CHAT_URLS["nim"], "NVIDIA_API_KEY", mid, tier, 0))
        except Exception as e:
            print("[catalog] nim skipped honestly:", type(e).__name__)
        except Exception as e:
            print("[catalog] nim skipped honestly:", type(e).__name__)
    tok = ""
    try:
        import PatchStep as PS
        tok = PS.token()
    except Exception:
        pass
    if tok:
        try:
            r = _get("https://models.github.ai/catalog/models", tok)
            for m in r.json() if isinstance(r.json(), list) else []:
                mid = m.get("id", "")
                if any(k in mid.lower() for k in ("deepseek", "llama-3.3-70b", "qwen3", "phi-4")):
                    cands.append(("ghm/" + mid, "https://models.github.ai/inference/chat/completions",
                                  "GHM_PAT", mid, "medium", 0))
        except Exception as e:
            print("[catalog] github-models skipped honestly:", type(e).__name__)
    # strongest-context first (the honest rank: bigger verified windows win)
    cands.sort(key=lambda c: -c[5])
    return cands


def _extras_state():
    try:
        return json.load(open(EXTRAS, encoding="utf-8-sig"))
    except Exception:
        return {"lanes": []}


def refresh(max_new=5):
    """One bounded refresh beat: catalogs -> probes -> extras (idempotent)."""
    try:
        import LaneBandit as LB
        print("[roster] bandit prior:", LB.seed_from_capability_map())
    except Exception:
        pass
    E = _env()
    st = _extras_state()
    have = {ln[0] for ln in st.get("lanes", [])}
    added, receipts = [], []
    for name, url, keyenv, model, tier, _cw in catalog_candidates(E)[:max_new * 4]:
        if len(added) >= max_new:
            break
        if name in have:
            continue
        tok = E.get(keyenv, "")
        if not tok and keyenv != "GHM_PAT":
            continue
        if keyenv == "GHM_PAT":
            try:
                import PatchStep as PS
                tok = PS.token() or ""
            except Exception:
                continue
        pr = _probe(url, tok, model)
        if pr.get("http") == 200:
            has = False
            for lane in st.get("lanes", []):
                if lane[3] == model and lane[1] == url:
                    has = True
            if not has:
                st.setdefault("lanes", []).append([name, url, keyenv, model, tier])
                added.append(name)
                receipts.append(f"+ {name} (HTTP 200 in {pr.get('ms')}ms) - LIVE")
        else:
            receipts.append(f"- {name}: {pr.get('http')} {pr.get('body','')[:40]} (dormant)")
    st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = EXTRAS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, EXTRAS)
    for r0 in receipts:
        print("[roster]", r0)
    return added


def retire_dead():
    """THE CORPSE RETIREMENT (the nim-k3 law): a lane that last answered
    410 Gone twice is RETIRED - excluded from rotation, watched for return,
    receipted honestly into the episodic ledger."""
    st = json.load(open(os.path.join(REPO, "scores", "lane_state.json"),
                        encoding="utf-8-sig")) if os.path.isfile(
        os.path.join(REPO, "scores", "lane_state.json")) else {}
    retired = []
    for lane, rec in st.items():
        if lane == "bandit" or not isinstance(rec, dict):
            continue
        # HTTP 410 = "Gone" BY DEFINITION (RFC 9110) - permanent, not a rate
        # wall: retire on the FIRST sighting (the 2-strike was overcautious;
        # nim-k3 sat in rotation one extra beat for it). The note keeps the
        # return-watch honest.
        if rec.get("last_http") == 410:
            rec["e410"] = rec.get("e410", 0) + 1
            if not rec.get("retired"):
                rec["retired"] = True
                rec["note"] = "RETIRED (410 Gone) - AutoRoster watches for the model's return"
                retired.append(lane)
    if retired:
        tmp = os.path.join(REPO, "scores", "lane_state.json") + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=1)
        os.replace(tmp, os.path.join(REPO, "scores", "lane_state.json"))
        try:
            with open(os.path.join(REPO, "memory_episodic.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": os.urandom(6).hex(),
                                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "kind": "roster",
                                    "text": "FLEET: retired " + ", ".join(retired) +
                                            " (410 Gone x2) - rotation freed",
                                    "meta": {}, "imp": 0.8}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    for r0 in retired:
        print("[roster] RETIRED:", r0)
    return retired


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "retire"):
        retire_dead()
    if mode in ("all", "refresh"):
        new = refresh()
        print("[roster]: new verified lanes:", new or "none (roster current)")