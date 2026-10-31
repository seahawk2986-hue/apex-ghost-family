"""ApexSkills v2 - certified skill library with retrieval, usage telemetry,
nightly re-certification, and demotion. Embedding-indexed via nomic.

API kept compatible with v1 (distill/curriculum) plus:
  find_relevant(objective, k=1)   -> most relevant certified skill (vector match)
  mark_used(skill_id)             -> usage counter (planner injections tracked)
  recertify(max_n, sandbox_fn)    -> dream-time re-verification; stale skills demote
"""

import json
import math
import os
import time

import requests

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(R, "Config", "SkillRegistry.json")
LEDGER = os.path.join(R, "Config", "RewardLedger.json")
QUEUE = os.path.join(R, "Config", "CurriculumQueue.txt")
EMBED_URL = os.environ.get("APEX_EMBED_URL", "http://127.0.0.1:1234/v1/embeddings")
EMBED_MODEL = os.environ.get("APEX_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
CORE = {"run_apex_evolution.py", "optimized_agent.py", "apex_ipce_engine.py",
        "apexmemory.py", "apexwebscraper.py", "apexnetscraper.py"}
MAX_SKILLS = 120


def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, path)
    except Exception:
        pass


def _embed(text):
    try:
        r = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "input": text[:3000]},
                          timeout=20)
        if r.status_code == 200:
            d = r.json().get("data", [])
            if d and isinstance(d, list):
                return d[0].get("embedding")
    except Exception:
        pass
    return None


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(x * x for x in b) ** 0.5 or 1.0
    return dot / (na * nb)


def distill(fn, intent, scr):
    """Certify a verified evolution into the skill library with an embedding."""
    try:
        lg = _load(LEDGER, {})
        best = float((lg.get(fn) or {}).get("best", 0) or 0)
        if best < 100.0:
            return None
        reg = _load(REG, {})
        # Registry dedupe: same source file refreshes its latest skill instead of piling up.
        for k, v in reg.items():
            if v.get("source") == fn and not v.get("demoted"):
                v["intent"] = intent[:200]
                v["reward"] = scr
                v["best"] = best
                v["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _vec = _embed(intent)
                if _vec:
                    v["vec"] = _vec
                _save(REG, reg)
                return k
        sid = f"{fn}@{time.strftime('%Y%m%d_%H%M%S')}"
        entry = {"source": fn, "intent": intent[:200], "reward": scr, "best": best,
                 "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "uses": 0, "last_used": None,
                 "last_verified": None, "demoted": False}
        _vec = _embed(intent)
        if _vec:
            entry["vec"] = _vec
        reg[sid] = entry
        if len(reg) > MAX_SKILLS:
            oldest = sorted((k for k, v in reg.items() if not v.get("demoted")),
                            key=lambda k: reg[k].get("ts", ""))[:len(reg) - MAX_SKILLS]
            for k in oldest:
                reg.pop(k, None)
        _save(REG, reg)
        return sid
    except Exception:
        return None


def find_relevant(objective, k=1):
    """Most relevant NON-DEMOTED certified skill for an objective (cosine)."""
    try:
        reg = _load(REG, {})
        vec = _embed(objective)
        if not vec:
            return None
        scored = []
        for k, v in reg.items():
            if v.get("demoted"):
                continue
            if isinstance(v.get("vec"), list):
                scored.append((k, v, _cosine(vec, v["vec"])))
        scored = [s for s in scored if s[2] >= 0.35]
        scored.sort(key=lambda s: s[2], reverse=True)
        out = []
        for k, v, s in scored[:k]:
            out.append({"skill_id": k, "source": v.get("source"),
                        "intent": v.get("intent"), "similarity": round(s, 3)})
        return out[0] if out else None
    except Exception:
        return None


def mark_used(skill_id, injected_text=None):
    """Usage telemetry: which certified skills actually influence evolution."""
    try:
        reg = _load(REG, {})
        v = reg.get(skill_id)
        if v is None: return
        v["uses"] = int(v.get("uses", 0)) + 1
        v["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save(REG, reg)
    except Exception:
        pass


def recertify(max_n=5, sandbox_fn=None):
    """Re-run each newest N skill's SOURCE through the sandbox (dream-time).
    CRASHED sources demote the skill before it can mislead the planner.
    Backfills embeddings for pre-v2 entries."""
    try:
        reg = _load(REG, {})
        entries = [(k, v) for k, v in reg.items() if not v.get("demoted")]
        entries.sort(key=lambda kv: kv[1].get("ts", ""), reverse=True)
        checked, demoted = 0, 0
        for k, v in entries[:max_n]:
            src = v.get("source", "")
            p = os.path.join(R, src)
            if not os.path.exists(p):
                v["demoted"] = True; v["demote_reason"] = "source file missing"
                demoted += 1; continue
            if not isinstance(v.get("vec"), list):
                _vec = _embed(v.get("intent", ""))
                if _vec: v["vec"] = _vec
            if sandbox_fn is not None:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _code = f.read()
                    _r = sandbox_fn(src, _code)
                    checked += 1
                    if _r.get("status") == "SUCCESS":
                        v["last_verified"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        v["demoted"] = True
                        v["demote_reason"] = f"source crashed in sandbox: {str(_r.get('error'))[:80]}"
                        demoted += 1
                except Exception as e:
                    v["demote_reason"] = f"recert error: {e}"
            if checked >= max_n and demoted >= 0:
                pass
            if checked >= max_n:
                break
        _save(REG, reg)
        return {"checked": checked, "demoted": demoted, "registry_size": len(reg)}
    except Exception as e:
        return {"error": str(e)[:80]}


def curriculum(top=3):
    """Self-issued curriculum proposals, from real evidence only."""
    props = []
    try:
        try:
            with open(os.path.join(R, "Config", "BenchmarkHistory.json"), "r", encoding="utf-8") as f:
                bh = json.load(f)[-1]
            w, s = bh.get("weakest_dimension"), bh.get("weakest_score", 1.0)
            if w and s is not None and s < 0.8:
                props.append(f"Strengthen weakest measured dimension '{w}' (score {s}) - "
                             f"run diagnosis drills and address the gap this cycle")
        except Exception:
            pass
        lg = _load(LEDGER, {})
        try:
            all_f = [f for f in os.listdir(R) if f.lower().endswith(".py") and f.lower() not in CORE]
        except Exception:
            all_f = []
        stale = sorted(((f, (lg.get(f) or {}).get("attempts", 0)) for f in all_f),
                       key=lambda x: x[1])[:3]
        for f, a in stale:
            if a <= 1:
                props.append(f"Explore {f}: only {a} attempt(s) so far - diversify experience")
        try:
            import sys as _sys
            if R not in _sys.path:
                _sys.path.insert(0, R)
            from ApexMemory import ApexMemory
            mem = ApexMemory()
            err_fns = sorted({(e.get("meta") or {}).get("file")
                              for e in mem.recent_events(30, kind="error")
                              if (e.get("meta") or {}).get("file")})
            for f in err_fns[:2]:
                props.append(f"Retry {f} with a smaller, more surgical change (recent failure lesson)")
        except Exception:
            pass
        try:
            with open(QUEUE, "r", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        props.append(f"Human-requested objective: {line}")
        except Exception:
            pass
    except Exception:
        pass
    return props[:top]


if __name__ == "__main__":
    reg = _load(REG, {})
    print(json.dumps({"skills": len(reg), "curriculum": curriculum()}, indent=2))