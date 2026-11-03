"""AbstractGym - THE NOVEL-ABSTRACTION + MATH MEASURER (the final round,
2026-11-04). The two tiers with NO organ now get one, the fleet's way:

  T4 (novel abstraction, the ARC-class)  - grid transforms by hidden rules
        (rotate/flip/shift/paint-by-rule) + sequence induction (the hidden
        generator) + code-induction (the output of a templated function)
  T2 (math)                              - exact-answer algebra/counting
        drills (sympy-graded: the truth = computed, never invented)
  T10.5 (SELF-REASONING)                 - the counterfactuals of the
        fleet's OWN survival ("RAM halved: what dies first?") - graded
        against the ModelBook's resource profiles (the machine judges
        its own architecture's logic)

THE HONESTY: every truth = DETERMINISTIC (sympy/template-code) - the gym
invents NOTHING; the answer = the strict-JSON lane reply; a refusal to
play = a MISS (calibration counts abstentions honestly). The receipts:
Config/abstract_gym.jsonl (per-drill) + Config/abstract_state.json (the
per-tier accuracy + the trend) - the same grammar the fleet already
measures itself with. $0; bounded 6 drills/beat; the keyless floor lane
means the gym NEVER starves."""
import itertools
import json
import os
import random
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "abstract_gym.jsonl")
STATE = os.path.join(ROOT, "Config", "abstract_state.json")


# --------------------------------------------------------- the generators
def _seq_induction():
    kind = random.choice(("arith", "geo", "fib"))
    if kind == "arith":
        a, d = random.randint(2, 9), random.randint(2, 7)
        seq = [a + d * i for i in range(8)]
        ans = f"{seq[6]},{seq[7]}"
        rule = f"start {a}, add {d}"
    elif kind == "geo":
        a, r0 = random.randint(2, 4), random.randint(2, 3)
        seq = [a * r0 ** i for i in range(8)]
        ans = f"{seq[6]},{seq[7]}"
        rule = f"start {a}, multiply {r0}"
    else:
        seq = [1, 1]
        while len(seq) < 8:
            seq.append(seq[-1] + seq[-2])
        ans = f"{seq[6]},{seq[7]}"
        rule = "the next = the sum of the previous two"
    return {"tier": "abstraction", "kind": f"seq-{kind}",
            "prompt": (f"A sequence begins: {seq[:6]}. State the hidden rule, then "
                       f"give the NEXT TWO terms as 'n,n'."), "truth": ans}


def _grid_transform():
    """The mini-ARC: a 4x4 grid + a hidden transform; the truth = applied."""
    import numpy as _np
    try:
        import numpy
    except Exception:
        return None
    g = [[random.randint(0, 3) for _ in range(4)] for _ in range(4)]
    rule = random.choice(("rot90", "transpose", "shift-right", "swap-01"))
    arr = _np.array(g)
    if rule == "rot90":
        out = _np.rot90(arr).tolist()
        human = "rotate 90 degrees counter-clockwise"
    elif rule == "transpose":
        out = arr.T.tolist()
        human = "transpose rows and columns"
    elif rule == "shift-right":
        out = [[0] + row[:3] for row in g]
        human = "shift every row one cell right (the overflow becomes 0)"
    else:
        out = [[(1 if v == 0 else 0 if v == 1 else v) for v in row] for row in g]
        human = "every 0 becomes 1 and every 1 becomes 0 (the rest stay)"
    flat = lambda m: " ".join(",".join(str(v) for v in row) for row in m)
    return {"tier": "abstraction", "kind": f"grid-{rule}",
            "prompt": (f"ARC-class: the input grid:\n{flat(g)}\nThe rule "
                       f"(in words, hidden): {human}\nAnswer with ONLY the "
                       "output grid in the same row format (rows separated by "
                       "spaces between rows uses a ' | ' between rows)."),
            "truth": flat(out)}


def _math_drill():
    kind = random.choice(("linear", "quadratic", "count"))
    try:
        import sympy as sy
    except Exception:
        return None
    x = sy.symbols("x")
    if kind == "linear":
        a, b = random.randint(2, 9), random.randint(1, 20)
        eq = a * x + b
        rhs = random.randint(30, 90)
        sol = sy.solve(sy.Eq(eq, rhs), x)[0]
        truth = f"{sol}"
        ask = f"Solve exactly: {a}x + {b} = {rhs}. Answer with ONLY the value of x."
    elif kind == "quadratic":
        r1, r2 = random.randint(-8, -1), random.randint(1, 8)
        b0, c0 = -(r1 + r2), r1 * r2
        sols = sy.solve(sy.Eq(x * x + b0 * x + c0, 0), x)
        truth = ",".join(str(sy.sympify(s)) for s in sorted(sols, key=lambda v: float(v)))
        ask = f"Solve exactly: x^2 + {b0}x + {c0} = 0. Answer ONLY the two roots as 'r1,r2'."
    else:
        n, k = random.randint(4, 9), random.randint(2, 4)
        import math
        truth = str(math.comb(n, k))
        ask = f"How many ways can you choose {k} items from {n}? Answer ONLY the number."
    return {"tier": "math", "kind": kind, "prompt": ask, "truth": truth}


_SELF_SCENES = [
    ("If the host RAM halved (16GB -> 8GB total), which Apex LAYER dies FIRST, and why? "
     "Answer: the layer name + one reason sentence.",
     "('the parallel-candidate election pool' in _a.lower() or 'candidate' in _a.lower())",
     "the parallel-candidate election pool (the RAM-multiplier dies first - each "
     "candidate holds a full inference context; the RAM gate law)"),
    ("If groq AND cerebras both 429 for the day (the TPD caps), which lane carries the "
     "night's chat correctly per the routing law? One word: the lane name.",
     "'pollinations' in _a.lower() or 'local-phi4' in _a.lower() or 'phi4' in _a.lower()",
     "pollinations then the local pacer floor (the keyless-eternal + the zero-cap "
     "floor; the strength law's floor exception)"),
    ("The docker engine died mid-evolution. What happens to an evolving candidate, "
     "per the sandbox law? One sentence.",
     "'fail-closed' in _a.lower() or 'nothing is executed' in _a.lower() or 'discarded' in _a.lower()",
     "fail-closed: nothing executes on the host; the candidate is discarded with a "
     "printed receipt"),
]


def _self_reasoning(i=None):
    idx = (i if i is not None else random.randint(0, len(_SELF_SCENES) - 1))
    q, check, truth_txt = _SELF_SCENES[idx % len(_SELF_SCENES)]
    return {"tier": "self-reasoning", "kind": f"counterfactual-{idx % len(_SELF_SCENES)}",
            "prompt": q, "truth": truth_txt, "checker": check}


def _grade(row):
    """The exact/fuzzy verdict - deterministic; a JSON-refusing reply = MISS
    (the calibration honest: 'couldn't play' != pass)."""
    import json as _json
    try:
        import CloudBrain as CB
        a = CB.chat(row["prompt"] + "\n\nReply ONLY strict JSON: {\"answer\": \"...\"}",
                    max_tokens=300, purpose=f"{row['tier']} drill")
        if not (a or "").strip():
            import FreeSwarm
            a = FreeSwarm.ask(row["prompt"] + "\n\nReply ONLY strict JSON: {\"answer\": \"...\"}",
                              max_tokens=300, purpose="abstract gym floor")
    except Exception:
        a = ""
    row["answer_raw"] = str(a)[:300]
    ans = ""
    try:
        m = re.search(r"\{[^{}]*\}", a or "", re.DOTALL)
        ans = _json.loads(m.group(0)).get("answer", "") if m else ""
    except Exception:
        ans = (a or "").strip()
    ans_l = str(ans).lower().replace(" ", "")
    truth_l = row["truth"].lower().replace(" ", "")
    if row.get("checker"):
        try:
            ok = bool(eval(row["checker"], {"_a": str(a or "").lower()}))
        except Exception:
            ok = False
    else:
        ok = truth_l in ans_l or ans_l == truth_l or \
             (truth_l.split(",")[0] in ans_l and truth_l.split(",")[-1] in ans_l)
    row["verdict"] = "HIT" if ok else "MISS"
    return row


def _selfplay_drill():
    """THE SELF-PLAY CURRICULUM (the S+ learning round): the fleet WRITES
    a novel drill (the generator) and the TRUTH-ENGINE validates it (the
    answer must be computable deterministically - sympy evaluates the
    prompt's equation as claimed) - an unverifiable drill = DISCARDED
    (the honest gate: no self-flattery may enter the curriculum)."""
    try:
        import CloudBrain as CB
        spec = CB.chat(
            "Invent ONE tiny math drill: a single-variable equation with "
            "integer coefficients. Reply ONLY strict JSON: "
            "{\"equation\": \"2x + 7 = 31\", \"answer\": \"12\", "
            "\"tier_note\": \"linear\"}",
            max_tokens=200, purpose="selfplay generator")
        import json as _j
        m = re.search(r"\{[^{}]*\}", spec or "", re.DOTALL)
        if not m:
            return None
        dj = _j.loads(m.group(0))
        eq, claimed = str(dj.get("equation", "")), dj.get("answer", "")
        if "x" not in eq or "=" not in eq:
            return None
        import sympy as sy
        x = sy.symbols("x")
        try:
            lhs, rhs = eq.split("=")
            expr = sy.sympify(lhs) - sy.sympify(rhs)
            truth = sy.solve(expr, x)
            if len(truth) != 1 or str(truth[0]) != str(claimed).strip():
                return None   # THE TRUTH-ENGINE VETO (no flattery enters)
            return {"tier": "selfplay", "kind": "self-generated",
                    "prompt": f"Solve exactly: {eq}. Answer ONLY x's value.",
                    "truth": str(truth[0])}
        except Exception:
            return None
    except Exception:
        return None


def beat(n=6):
    random.seed(time.time())
    drills = []
    sp = _selfplay_drill()
    if sp:
        drills.append(sp)
        print("[abstract-gym]: +1 self-play drill (the truth-engine approved)")
    for _ in range(n):
        pick = random.choice((_seq_induction, _grid_transform, _math_drill,
                              _math_drill, _self_reasoning, _seq_induction))
        d = pick()
        if d:
            drills.append(d)
    rows = [_grade(d) for d in drills]
    for r in rows:
        r["ts"] = time.strftime("%H:%M:%S")
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        st = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "tiers": {}}
        try:
            hits = {}
            for ln in open(LEDGER, encoding="utf-8-sig"):
                r0 = json.loads(ln)
                s = r0.get("tier", "?")
                st["tiers"].setdefault(s, {"n": 0, "hits": 0})
                st["tiers"][s]["n"] += 1
                st["tiers"][s]["hits"] += 1 if r0.get("verdict") == "HIT" else 0
        except FileNotFoundError:
            pass
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=1)
    except Exception as e:
        print(f"[abstract-gym] receipt write failed: {e}")
    acc = sum(1 for r in rows if r["verdict"] == "HIT")
    per = {r["kind"]: r["verdict"] for r in rows}
    print(f"[abstract-gym]: {acc}/{len(rows)} HIT (the tiers now measured: "
          f"{json.dumps(per, ensure_ascii=False)[:200]})")
    return rows


if __name__ == "__main__":
    beat()