"""ApexSkills - Skill certification + self-issued curriculum.

'distill' certifies successfully-evolved files into a skill registry
(Skills are pointers + metadata: source file, intent, verified reward).
'curriculum' proposes self-issued objectives from real data:
   - neglected files (bandit exploration)
   - failure lessons (targeted retries with smaller scope)
   - the human's own idea queue (Config/CurriculumQueue.txt)
"""

import json
import os
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(R, "Config", "SkillRegistry.json")
LEDGER = os.path.join(R, "Config", "RewardLedger.json")
QUEUE = os.path.join(R, "Config", "CurriculumQueue.txt")
CORE = {"run_apex_evolution.py", "optimized_agent.py", "apex_ipce_engine.py",
        "apexmemory.py", "apexwebscraper.py", "apexnetscraper.py"}


def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except Exception:
        pass


def distill(fn, intent, scr):
    """Certify a verified evolution as a skill. Only reward-certified files."""
    try:
        lg = _load(LEDGER, {})
        best = float((lg.get(fn) or {}).get("best", 0) or 0)
        if best < 100.0:
            return None
        reg = _load(REG, {})
        sid = f"{fn}@{time.strftime('%Y%m%d_%H%M%S')}"
        reg[sid] = {"source": fn, "intent": intent[:200], "reward": scr,
                    "best": best, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save(REG, reg)
        return sid
    except Exception:
        return None


def curriculum(top=3):
    """Self-issued curriculum proposals, from real evidence only."""
    props = []
    try:
        # Weakest measured dimension first (nightly benchmark data, real numbers)
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
        # Bandit: neglected files
        stale = sorted(((f, (lg.get(f) or {}).get("attempts", 0)) for f in all_f),
                       key=lambda x: x[1])[:3]
        for f, a in stale:
            if a <= 1:
                props.append(f"Explore {f}: only {a} attempt(s) so far - diversify experience")
        # Failure lessons: targeted retries
        try:
            sys_path = R
            import sys as _sys
            if sys_path not in _sys.path:
                _sys.path.insert(0, sys_path)
            from ApexMemory import ApexMemory
            mem = ApexMemory()
            err_fns = sorted({(e.get("meta") or {}).get("file")
                              for e in mem.recent_events(30, kind="error")
                              if (e.get("meta") or {}).get("file")})
            for f in err_fns[:2]:
                props.append(f"Retry {f} with a smaller, more surgical change (recent failure lesson)")
        except Exception:
            pass
        # Human idea queue
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
    print(json.dumps({"skills": len(_load(REG, {})), "curriculum": curriculum()}, indent=2))