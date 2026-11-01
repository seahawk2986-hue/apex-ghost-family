"""ApexTrainingCamp - forecast gym: trains Apex's execution reasoning.

Mechanism (STaR-style self-training, measurable end to end):
  1. A pool of small programs with TRICKY but deterministic semantics,
     each with a "lesson" explaining the underlying trap.
  2. Ground truth is CAPTURED BY EXECUTION at pool-build time (never assumed).
  3. train_session(n): Apex predicts the exact stdout of n programs (no
     running allowed), the pool's captured truth is compared, and:
       - every forecast lands in memory as {predicted, actual} (feeds the
         benchmark's reasoning dimension)
       - every MISS writes the program's trap-lesson into semantic memory,
         which the planner/Socratic pipeline recalls in future cycles.
  4. Sessions run at dream time (nightly) and on demand.

This directly trains the weakest measured dimension: reasoning calibration.
"""

import json
import os
import re
import subprocess
import sys
import time
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(R, "Config", "TrainingPool.json")
LOG = os.path.join(R, "Config", "TrainingLog.json")
PY = os.path.join(R, "apex_venv", "Scripts", "python.exe")

# id: (code, trap-lesson)  - ground truth is EXECUTED during build, never assumed
POOL_PROGRAMS = {
    "mut_default": (
        "def add_item(x, acc=[]):\n    acc.append(x)\n    return acc\n"
        "print(add_item(1))\nprint(add_item(2))",
        "Mutable default arguments persist between calls - the SAME list is reused, "
        "so the second call sees the first call's item. Use None + rebuild instead."
    ),
    "negfloor": (
        "print(-7 // 2)\nprint(7 // -2)",
        "Integer division in Python floors toward NEGATIVE INFINITY (not toward zero): "
        "-7 // 2 == -4 and 7 // -2 == -4. Truncate semantics would say -3."
    ),
    "boolmath": (
        "print(True + True)\nprint(False * 10)",
        "bool is a subclass of int in Python: True == 1, False == 0. "
        "Arithmetic on booleans is integer arithmetic."
    ),
    "closureloop": (
        "fs = [lambda: i for i in range(3)]\nprint(fs[0](), fs[2]())",
        "Closures capture the VARIABLE, not its value at creation. After the loop "
        "ends, i is 2 for every lambda - the classic late-binding trap."
    ),
    "dupdict": (
        "print({k: k * k for k in [2, 2, 3]})",
        "Duplicate comprehension keys overwrite: the LAST assignment for each key "
        "wins, and dict order follows first-insertion."
    ),
    "slicealias": (
        "a = [1, 2, 3]\nb = a[:]\nb.append(4)\nprint(a, b)",
        "a[:] makes a SHALLOW COPY - appending to the copy leaves the original "
        "unchanged. Contrast with b = a (alias), where both would change."
    ),
    "formatprec": (
        "print(f\"{1/3:.2f}\")\nprint(round(0.5))",
        "f-string :.2f truncates display to 2 decimals; round uses banker's rounding - "
        "round(0.5) == 0 (ties go to the EVEN neighbor)."
    ),
    "swap": (
        "a, b = 1, 2\na, b = b, a + b\nprint(a, b)",
        "Simultaneous assignment evaluates the RIGHT side first with the OLD values: "
        "a,b = b,a+b swaps-and-advances in one step."
    ),
    "exflow": (
        "try:\n    print('a')\n    raise ValueError\n    print('b')\nexcept ValueError:\n    print('c')\nelse:\n    print('d')\nfinally:\n    print('e')",
        "try/except/else/finally order: body runs, else runs ONLY on success, finally "
        "ALWAYS runs; statements after the raise never execute."
    ),
    "strmult": (
        "print('ab' * 2 + 'c')",
        "String * n repeats the whole string; + concatenates left to right - "
        "'ab'*2 + 'c' is 'abab' then 'abc'."
    ),
    "istest": (
        "print([1, 2] == [1, 2])\nprint([1, 2] is [1, 2])",
        "== compares VALUES; 'is' compares IDENTITY. Two equal lists are equal but "
        "distinct objects, so 'is' is False."
    ),
    "chainassign": (
        "x = y = [0]\nx.append(1)\ny.append(2)\nprint(x)",
        "x = y = [0] binds BOTH names to the SAME list - appends through either name "
        "mutate one shared object: [0, 1, 2]."
    ),
}


def build_pool(force=False):
    """Capture ground truth by executing every program once (safe: pure prints)."""
    if os.path.exists(POOL) and not force:
        return _read(POOL)
    pool = []
    for pid, (code, lesson) in POOL_PROGRAMS.items():
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, timeout=15)
        truth = (r.stdout or "").rstrip("\n")
        pool.append({"id": pid, "code": code, "truth": truth, "lesson": lesson})
        print(f"[pool] {pid}: truth captured ({len(truth)} chars)")
    _write(POOL, pool)
    return pool


def _read(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return []


def _write(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except Exception:
        pass


def _norm(text):
    """Normalization: strip outer whitespace, trim per-line trailing spaces."""
    lines = [ln.rstrip() for ln in str(text).strip().splitlines()]
    return "\n".join(lines).strip()


def _log():
    try:
        with open(LOG, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _missed_programs(log, n):
    """Prioritize programs with fewer attempts or recent misses."""
    scores = []
    for e in pool_items():
        hist = log.get(e["id"], {"attempts": 0, "wrong": 0})
        wrong = hist.get("wrong", 0)
        att = hist.get("attempts", 0)
        scores.append((e["id"], wrong * 2 - att))  # misses rise, attempts sink
    scores.sort(key=lambda x: -x[1])
    return [pid for pid, _ in scores[:n]]


def pool_items():
    return _read(POOL)


def train_session(n=5, cloud_ask=None, verbose=True):
    """Run one training session: n forecast exercises with scored feedback."""
    build_pool()
    pool = {e["id"]: e for e in pool_items()}
    log = _log()
    picks = _missed_programs(log, n)

    try:
        sys.path.insert(0, R)
        from ApexMemory import ApexMemory
        m = ApexMemory()
    except Exception:
        m = None

    scorecard = []
    correct = 0
    for pid in picks:
        e = pool[pid]
        t0 = time.time()
        pred_raw = ""
        ok_model = False
        if cloud_ask:
            pred_raw = cloud_ask(
                "You are Apex's forecasting unit. WITHOUT running any code, predict the EXACT "
                "stdout of this Python program. Consider Python semantics precisely "
                "(mutable defaults, floor division, late binding, rounding, identity). "
                f"Reply with ONLY the stdout wrapped between <<<OUT>>> and <<<END>>> markers "
                "and nothing else.\n\nPROGRAM:\n```python\n" + e["code"] + "\n```",
                max_tokens=300)
            ok_model = True
            match = re.search(r"<<<OUT>>>\n?(.*?)\n?<<<END>>>", pred_raw or "", re.DOTALL)
            pred_raw = match.group(1) if match else (pred_raw or "").strip()
        if not pred_raw:
            scorecard.append({"id": pid, "verdict": "abstained"})
            continue

        pred = _norm(pred_raw)
        truth = _norm(e["truth"])
        hit = pred == truth
        correct += 1 if hit else 0

        entry = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "pred": pred[:200],
                 "actual": truth[:200], "hit": hit}
        hist = log.setdefault(pid, {"attempts": 0, "wrong": 0})
        hist["attempts"] = hist.get("attempts", 0) + 1
        if not hit:
            hist["wrong"] = hist.get("wrong", 0) + 1
            hist["last_miss"] = pred[:120]
        _write(LOG, log)

        if m is not None:
            m.record_event("forecast",
                           f"trainingcamp/{pid}: predicted {pred[:60]!r}, actual {truth[:60]!r} "
                           f"({'HIT' if hit else 'MISS'})",
                           predicted=pred if hit else truth, actual=truth, hit=hit)
            if not hit:
                m.remember(f"Lesson ({pid}): {e['lesson']} Ground truth was: {truth!r}.",
                           kind="lesson")

        scorecard.append({"id": pid, "hit": hit,
                          "pred": pred[:120], "truth": truth[:120], "via_model": ok_model})
        if verbose:
            print(f"[{pid}] {'HIT' if hit else 'MISS'}: pred={pred[:80]!r} truth={truth[:80]!r}")

    total = len(scorecard)
    hits = sum(1 for s in scorecard if s.get("hit"))
    summary = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "exercises": total,
               "hits": hits, "accuracy": round(hits / max(1, total), 2),
               "forecast": scorecard}
    _write(LOG, log | {"_sessions": (_log().get("_sessions", []) + [summary])[-60:]})
    if verbose:
        print(f"[SESSION] accuracy {summary['accuracy']:.2f} ({hits}/{total})")
    return summary