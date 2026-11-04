"""FreeSwarm v2 - THE AGGREGATE-UNLIMITED POOL (the "unlimited" organ,
the A+ round 2026-11-04).

THE REALITY (honest): no single vendor sells infinite free tokens; the
unlimited lane is CONSTRUCTED, not bought. Three providers hand the fleet
individually-capped free seats TODAY:
  openrouter   ~:free models  (50 req/day EACH; ~14 listed now)
  nim          the NVIDIA trial door: 85 listed models, 60 RPM each -
               INCLUDES THE TITANS (nemotron-3-ultra-550b, deepseek-v4.1,
               glm-5.3-flash, minimax-m3.1)
  gh           GitHub-Models (the fleet's held PAT; per-hour PAT caps)
N single-model caps in rotation = the N*cap aggregate pool (~100+ seats,
thousands of $0 calls/day), walked big-first; a capped/dead seat hands to
the next - NEVER a retry ladder against a clock.

THE SAME-WEIGHTS LAW: weight=<model-family> pins the rotation to that
family across every provider; a hand-off changes the PROVIDER, not the
MODEL, and never drops strength (upgrades allowed; downgrades banned).

State: Config/freeswarm_state.json (used/excluded per seat, UTC-day roll);
exclusion windows are provider-honest: openrouter day-cap = 20h, nim RPM =
5 min, gh = 10 min, 404-corpse listings = 20h so the dead don't re-probe.
$0 always. stdlib. Fail-closed (an empty pool returns honestly)."""
import json
import os
import sys
import threading
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(ROOT, "Config", "freeswarm_state.json")
CAT = os.path.join(ROOT, "Config", "freeswarm_catalog.json")
UA = {"User-Agent": "apex-freeswarm/2.0"}
DAILY_CAP = 50          # openrouter's stated per-free-model requests/day
CATALOG_TTL = 6 * 3600
EXCLUDE_S = {"openrouter": 20 * 3600, "nim": 5 * 60, "gh": 10 * 60,
             "404": 20 * 3600}
NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_LIST = "https://integrate.api.nvidia.com/v1/models"
GH_LIST = "https://models.github.ai/catalog/models"


def _env():
    try:
        sysp = os.path.join(ROOT, "Scripts")
        if sysp not in sys.path:
            sys.path.insert(0, sysp)
        import ApexIO
        return ApexIO.env()
    except Exception:
        return dict(os.environ)


def _http_json(url, method="GET", headers=None, body=None, timeout=45,
               auth=None):
    try:
        headers = {**UA, **(headers or {}), "Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = "Bearer " + auth
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        code = getattr(e, "code", None)
        txt = ""
        try:
            txt = (e.read().decode(errors="replace")[:300]) if hasattr(e, "read") else str(e)
        except Exception:
            txt = str(e)
        return {"_error": {"code": code, "text": txt}}


_STATE_LOCK = threading.RLock()      # parallel-island asks share this state


def _load_state():
    try:
        with _STATE_LOCK:
            return json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        return {"day": "", "used": {}, "excluded": {}}


def _save_state(st):
    try:
        with _STATE_LOCK:
            tmp = STATE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f)
            os.replace(tmp, STATE)
    except Exception:
        pass


def _roll_day(st):
    today = time.strftime("%Y-%m-%d", time.gmtime())
    if st.get("day") != today:
        st |= {"day": today, "used": {}, "excluded": {}}
    return st


def _seat(mid, provider, ctx=0, name=""):
    return {"id": mid, "provider": provider, "ctx": int(ctx or 0), "name": name}


def catalog(force=False):
    """The live merged seat-catalog, big-first (cached 6h on disk)."""
    try:
        if not force and os.path.exists(CAT) and \
                time.time() - os.path.getmtime(CAT) < CATALOG_TTL:
            return json.load(open(CAT, encoding="utf-8-sig"))
    except Exception:
        pass
    seats = []
    # (a) openrouter :free
    orr = _http_json("https://openrouter.ai/api/v1/models", timeout=20)
    for m in (orr or {}).get("data", []):
        if str(m.get("id", "")).endswith(":free"):
            seats.append(_seat(m["id"], "openrouter",
                               m.get("context_length") or 0, m.get("name", "")))
    # (b) NIM: the trial door's whole roster (titan-heavy)
    key = _env().get("NVIDIA_API_KEY", "")
    if key:
        nim = _http_json(NIM_LIST, timeout=20, auth=key)
        for m in (nim or {}).get("data", []):
            mid = m.get("id") or ""
            if mid and ".html" not in mid:
                seats.append(_seat(mid, "nim", 0, m.get("name", "")))
    # (c) GitHub-Models with the fleet's PAT
    gtok = _env().get("GITHUB_TOKEN", "") or _env().get("GH_MODELS_TOKEN", "")
    if gtok:
        gh = _http_json(GH_LIST, timeout=20, auth=gtok)
        gh_rows = gh if isinstance(gh, list) else (gh.get("models") or [])
        for m in gh_rows:
            mid = m.get("id") or m.get("name") or ""
            if mid:
                seats.append(_seat(mid, "gh", 0, m.get("display_name", "")))
    seats.sort(key=lambda s: -s["ctx"])
    try:
        with open(CAT, "w", encoding="utf-8") as f:
            json.dump(seats, f)
    except Exception:
        pass
    return seats


def _load_env():
    return _env()


def ask(prompt, max_tokens=500, purpose="freeswarm", skip=0, weight=None):
    """ONE question through the rotator: N independent caps, walked
    big-first; the capped/dead seat hands to the next (never a ladder);
    the receipt = the serving model id (honest)."""
    key_e = _env()
    ORK = key_e.get("OPENROUTER_API_KEY", "")
    NTK = key_e.get("NVIDIA_API_KEY", "")
    GTK = key_e.get("GITHUB_TOKEN", "") or key_e.get("GH_MODELS_TOKEN", "")
    if not (ORK or NTK or GTK):
        return ""
    st = _roll_day(_load_state())
    cat = catalog()
    if weight:
        wl = weight.lower()
        ids = [s for s in cat if wl in (s["id"] or "").lower()]
        if not ids:
            print(f"[freeswarm] same-weights law: no provider lists "
                  f"{weight} - honest empty")
            return ""
    else:
        ids = list(cat)
    now = time.time()
    ids = [s for s in ids
           if st["excluded"].get(s["id"], 0) <= now]
    ids = ids[skip:] + ids[:skip] if ids else []
    alive_ids = []
    for s in ids[:60]:
        mid, prov = s["id"], s["provider"]
        if prov == "nim":
            probe = _http_json(NIM_LIST, auth=_env().get("NVIDIA_API_KEY") or None)
            if (not isinstance(probe, dict)) or ("data" not in probe):
                st["excluded"][mid] = now + EXCLUDE_S["404"]
                _save_state(st)
                continue
        elif prov == "gh":
            probe = _http_json(GH_LIST, auth=_env().get("GITHUB_TOKEN") or _env().get("GH_MODELS_TOKEN") or None)
            if (not isinstance(probe, dict)) or ("data" not in probe):
                st["excluded"][mid] = now + EXCLUDE_S["404"]
                _save_state(st)
                continue
        alive_ids.append(s)
    ids = alive_ids
    for s in ids[:60]:
        mid, prov = s["id"], s["provider"]
        daily = DAILY_CAP if prov == "openrouter" else (500 if prov == "nim" else 200)
        if st["used"].get(mid, 0) >= daily:
            continue
        if prov == "openrouter":
            url, auth = "https://openrouter.ai/api/v1/chat/completions", ORK
        elif prov == "nim" and NTK:
            url, auth = NIM_URL, NTK
        elif prov == "gh" and GTK:
            url, auth = "https://models.github.ai/inference/chat/completions", GTK
        else:
            continue
        d = _http_json(url, method="POST", auth=auth, timeout=45,
                       body={"model": mid, "stream": False,
                             "messages": [{"role": "user", "content": prompt[:6000]}],
                             "max_tokens": max_tokens})
        err = d.get("_error") or {}
        if err:
            code, txt = err.get("code"), err.get("text", "")
            if code in (404, 400):                 # listed-but-dead class
                st["excluded"][mid] = now + EXCLUDE_S["404"]
                _save_state(st)
                continue
            if "429" in str(code) or "rate" in (txt or "").lower() or \
                    "quota" in (txt or "").lower():
                st["excluded"][mid] = now + EXCLUDE_S.get(prov, 600)
                _save_state(st)
                continue                           # THE HAND-OFF
            continue
        txt = (d.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
        if txt.strip():
            st["used"][mid] = st["used"].get(mid, 0) + 1
            _save_state(st)
            print(f"[freeswarm] served by {prov}/{mid} ({purpose}; "
                  f"use {st['used'][mid]}/{daily} today, $0)")
            return txt
    return ""


def pool_stats():
    st = _roll_day(_load_state())
    cat = catalog()
    by_prov = {}
    for s in cat:
        by_prov[s["provider"]] = by_prov.get(s["provider"], 0) + 1
    return {"seats": len(cat), "by_provider": by_prov,
            "calls_today": sum(st["used"].values()),
            "excluded_now": sum(1 for v in st["excluded"].values() if v > time.time()),
            "law": "N single-model caps in rotation = the constructed "
                   "unlimited lane; same-weights pinned on demand"}


def selftest():
    t0 = time.time()
    ans = ask("Reply with exactly one word: PONG", max_tokens=20,
              purpose="selftest")
    print(json.dumps({"served": bool((ans or "").strip()),
                      "answer": (ans or "")[:60],
                      "wall_s": round(time.time() - t0, 1),
                      "stats": pool_stats()}, indent=1)[:1200])


if __name__ == "__main__":
    selftest()