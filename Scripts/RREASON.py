"""RREASON - THE REASONING ORGAN of the recursive self-evolution core
(single file; $0; fleet-fed; 2026-11-03). The upgrade the constitution
demands: the genome is no longer arithmetic - it is an INFERENCE
PROGRAM (the strategy a swarm uses to think), and fitness lives on a
REASONING ARENA:

  THE WORLD   arena_inbox/*.json ({name, items:[{q, a}, ...]}) dropped
              by any free source (a swarm organ, a hunter, a human)
              becomes the arena; empty inbox = the builtin bench
              (deterministic arithmetic/sequence/letter/comparison
              items, gold-generated in this file - the loop never
              starves, the outsourcing never load-bears).
  THE GENOME  {rounds, debate, synth, refine, style, maxt, rate} - the
              strategy is evolvable: base ask -> optionally TWO-DIVERSE
              SEATS (debate) -> OPTIONAL SYNTHESIS -> refine rounds
              (critique+revise) -> extract 'ANSWER:'.
  THE TAX     fitness = ERROR on gold + COST: 0.05 per lane ask - the
              swarm evolves CAPABILITY-PER-COST (the frontier-scale
              honesty: cleverness measured against what it spends).
  RECURSION   every candidate strategy is scored by a subprocess of
              THIS core running itself against the live free lanes; a
              child crash kills a generation, never the lineage.
  LAWS  = RSEC's seven (receipts, $0, stop-stone, checkpoints, runaway
              caps, promotion-only-on-fitness, append-only ledger).

  CLI: python RREASON.py run [cycles] | eval <g.json> | status
       python RREASON.py rollback [k] | stop"""
import concurrent.futures
import copy
import json
import os
import random
import re
import subprocess
import sys
import time

HOME = os.environ.get("RREASON_HOME") or os.path.dirname(
    os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(HOME, "rreason_receipts.jsonl")
POOL = os.path.join(HOME, "rreason_pool")
STOPF = os.path.join(HOME, "RREASON_STOP")
GENOME_F = os.path.join(HOME, "rreason_genome.json")
INBOX = os.path.join(HOME, "arena_inbox")
POP = max(2, int(os.environ.get("RREASON_POP", "3")))
N_ITEMS = max(2, int(os.environ.get("RREASON_ITEMS", "8")))
EVAL_TIMEOUT = int(os.environ.get("RREASON_TIMEOUT", "1200"))

STYLES = (
    ("Answer the question. End with a line 'ANSWER: <final answer>'.\n\nQ: {q}"),
    ("Think step by step, briefly. End with a line 'ANSWER: <final "
     "answer>'.\n\nQ: {q}"),
    ("Work backwards from what the answer must satisfy. End with "
     "'ANSWER: <final answer>'.\n\nQ: {q}"),
    ("Break the question into sub-questions, settle each, then end with "
     "'ANSWER: <final answer>'.\n\nQ: {q}"),
)
KINDS = ("flip", "rounds", "style", "cost", "meta")


def _bench():
    """THE BUILTIN NEVER-STARVE ARENA (deterministic; gold computed
    right here - no trust, no network, no excuses)."""
    rng = random.Random(11)
    words = ("strawberry estate telescope meadow principle assembly "
             "corridor discovery).".split())
    ws = [w.strip(".,)")for w in words if w.strip(".,)")]
    items = []
    for i in range(12):
        k = i % 5
        if k == 0:
            a, b, c = [rng.randint(2, 12) for _ in range(3)]
            items.append({"q": f"What is {a} * {b} + {c}?", "a": a * b + c})
        elif k == 1:
            a, b = rng.randint(10, 99), rng.randint(2, 9)
            items.append({"q": f"What is {a} modulo {b}?", "a": a % b})
        elif k == 2:
            s, r = rng.randint(2, 9), rng.randint(2, 6)
            seq = [s + r * j for j in range(4)]
            items.append({"q": f"Next number: {', '.join(map(str, seq))}?",
                          "a": seq[3] + r})
        elif k == 3:
            w = rng.choice(ws)
            items.append({"q": f"How many letter 'e' in the word "
                               f"'{w}'? (letter count)", "a": w.count("e")})
        else:
            a, b, c, d = [rng.randint(1, 40) for _ in range(4)]
            left, right = a + b, c + d
            items.append({"q": f"Which is larger: {a}+{b} or {c}+{d}? "
                               f"Answer A or B.",
                          "a": "A" if left > right else "B"})
    return items


def _arena():
    try:
        files = sorted(f for f in os.listdir(INBOX) if f.endswith(".json"))
    except Exception:
        return ("builtin", _bench()[:N_ITEMS])
    for fn in reversed(files):
        try:
            t = json.load(open(os.path.join(INBOX, fn), encoding="utf-8"))
            items = t["items"]
            if (isinstance(items, list) and len(items) >= 2
                    and all(isinstance(it, dict) and "q" in it and "a" in it
                            for it in items)):
                rng = random.Random(len(items))
                return (str(t.get("name") or fn)[:60],
                        list(items)[:N_ITEMS])
        except Exception:
            continue
    return ("builtin", _bench()[:N_ITEMS])


def _norm(s):
    s = str(s).lower().strip().strip(".,!?")
    return re.sub(r"\s+", " ", s)


def _grade(ans, gold):
    a, g = _norm(ans), _norm(gold)
    if not a:
        return 0.0
    if a == g:
        return 1.0
    try:
        if abs(float(re.search(r"-?\d+(?:\.\d+)?", a).group())
               - float(re.search(r"-?\d+(?:\.\d+)?", g).group())) < 1e-6:
            return 1.0
    except Exception:
        pass
    ta, tg = set(a.split()), set(g.split())
    return 1.0 if ta and tg and len(ta & tg) / max(2, len(ta | tg)) > 0.8 \
        else 0.0


def _extract(text):
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    for l in reversed(lines):
        m = re.match(r"^answer\s*[:\-]\s*(.+)$", l, re.I)
        if m:
            return m.group(1).strip()
    if re.match(r"^answer\s*[:\-]", (lines[-1] if lines else ""), re.I):
        return (lines[-1] or "").split(":", 1)[-1].strip()
    return lines[-1] if lines else ""


def _ask(prompt, max_tokens, purpose, skip=0):
    import FreeSwarm as FS
    return (FS.ask(prompt, max_tokens=max_tokens, purpose=purpose,
                   skip=skip) or "")


def _reason_one(g, q, tag):
    """ONE ITEM through the strategy: the code version of the genome."""
    st = STYLES[g["style"] % len(STYLES)].format(q=q)
    asks = 0
    draft = _ask(st, g["maxt"], f"{tag}-base")
    asks += 1
    if g.get("debate"):
        a1 = draft
        a2 = _ask(f"Question: {q}\nGive the answer in one line, then "
                  "stop.", g["maxt"], f"{tag}-seat-B", skip=6)
        asks += 1
        if g.get("synth"):
            draft = _ask("Two independent advisors answered a question.\n"
                         f"Q: {q}\nA1: {_extract(a1)[:400]}\n"
                         f"A2: {_extract(a2)[:400]}\n"
                         "Silently pick or merge the better reasoning and "
                         f"reply END with 'ANSWER: <final>'.\nQ: {q}",
                         g["maxt"], f"{tag}-synth")
            asks += 1
        else:
            draft = a2 if random.random() < 0.5 else a1
    for _ in range(g.get("rounds", 1) - 1
                   + (1 if g.get("refine") else 0)):
        draft = _ask("Critique this draft for arithmetic or logic errors, "
                     "then output the corrected result.\n\n"
                     f"Q: {q}\nDraft: {draft[:600]}\n"
                     "End your reply with 'ANSWER: <final answer>'.",
                     g["maxt"], f"{tag}-refine")
        asks += 1
    return _extract(draft), asks


def _strategy_score(g):
    """THE ARENA: mean per-item error + THE COST TAX (0.05/ask)."""
    name, items = _arena()
    err, cost = 0.0, 0
    for it in items:
        ans, asks = _reason_one(g, it["q"], "arena")
        err += 1.0 - _grade(ans, it["a"])
        cost += asks
    return round(err / len(items) + 0.05 * cost, 6), name


def _seed():
    return {"gen": 0, "rate": 0.35, "rounds": 1, "debate": False,
            "synth": False, "refine": False, "style": 0, "maxt": 160}


def _etch(g):
    tmp = GENOME_F + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    os.replace(tmp, GENOME_F)


def _load_genome():
    try:
        g = json.load(open(GENOME_F, encoding="utf-8"))
        if not isinstance(g, dict) or "style" not in g:
            raise ValueError("bad")
        return g
    except Exception:
        g = _seed()
        _etch(g)
        return g


def _receipt(row):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _bandit():
    w = [0.22, 0.20, 0.18, 0.18, 0.22]
    try:
        rows = [json.loads(l) for l in
                open(LEDGER, encoding="utf-8-sig")][-300:]
    except Exception:
        return w
    tally = {}
    for r in rows:
        if r.get("ev") in ("PROMOTE", "DISCARD"):
            t = tally.setdefault(r.get("op", "flip"), [0, 0])
            t[0 if r["ev"] == "PROMOTE" else 1] += 1
    for i, k in enumerate(KINDS):
        t = tally.get(k)
        if t and t[0] + t[1] >= 3:
            w[i] *= 0.4 + 1.2 * t[0] / (t[0] + t[1])
    return w


def _mutate(g, rng, w):
    child = copy.deepcopy(g)
    kind = rng.choices(KINDS, weights=w)[0]
    if kind == "flip":
        key = rng.choice(("debate", "synth", "refine"))
        child[key] = not child.get(key)
        if key == "debate" and not child["debate"]:
            child["synth"] = False
    elif kind == "rounds":
        child["rounds"] = max(1, min(2, child["rounds"] +
                                     rng.choice((-1, 1))))
    elif kind == "style":
        child["style"] = (child["style"] + rng.choice((1, 2, 3))) % 4
    elif kind == "cost":
        child["maxt"] = max(60, min(360, child["maxt"]
                                    + rng.choice((-40, 40))))
    else:
        child["rate"] = round(rng.uniform(0.05, 0.7), 3)
    child["gen"] = g.get("gen", 0) + 1
    return child, kind


def _child_eval(path):
    try:
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "eval", path], capture_output=True, text=True,
                           timeout=EVAL_TIMEOUT)
        return json.loads(r.stdout.strip().splitlines()[-1])["score"]
    except Exception:
        return None


def mode_run(cycles=20, budget_s=1800, eps=1e-7):
    os.makedirs(POOL, exist_ok=True)
    g = _load_genome()
    parent, world = _strategy_score(g)
    strat = json.dumps({k: g[k] for k in ("rounds", "debate", "synth",
                                          "refine", "style", "maxt")})
    _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ev": "WAKE",
              "gen": g["gen"], "parent": parent, "world": world})
    print(f"[rreason]: waking gen {g['gen']} | arena '{world}' | "
          f"strategy {strat} | score {parent}")
    t_end = time.time() + budget_s
    for _ in range(cycles):
        if os.path.exists(STOPF):
            print("[rreason]: the stop-stone stands - halted")
            break
        if time.time() >= t_end:
            print("[rreason]: the budget closes the loop")
            break
        t0 = time.time()
        w = _bandit()
        kids = [_mutate(g, random.Random(), w) for _ in range(POP)]
        paths = []
        for kid, _k in kids:
            p = os.path.join(POOL, f"cand_{os.getpid()}_"
                             f"{random.randint(1, 10 ** 6)}.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(kid, f)
            paths.append(p)
        with concurrent.futures.ThreadPoolExecutor(max_workers=POP) as ex:
            scores = list(ex.map(_child_eval, paths))
        lat = round(time.time() - t0, 3)
        best, champ, bop, bname = None, None, "-", "-"
        for (kid, kind), p, sc in zip(kids, paths, scores):
            try:
                os.remove(p)
            except Exception:
                pass
            _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ev":
                      "TRIED", "gen": kid["gen"], "op": kind,
                      "child": sc, "lat": lat})
            if sc is not None and (best is None or sc < best):
                best, champ, bop = sc, kid, kind
        if champ is None:
            print("[rreason]: the brood died in the mirror (the lineage "
                  "outlives it)")
            continue
        wname, items = _arena()          # the champion's honest re-read
        kept = best < parent - eps
        if kept:
            g = champ
            parent = best
            _etch(g)
            with open(os.path.join(POOL, f"gen_{g['gen']}.json"), "w",
                      encoding="utf-8") as f:
                json.dump(g, f, indent=1)
        _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "ev": "PROMOTE" if kept else "DISCARD", "gen":
                  champ["gen"], "op": bop, "child": best,
                  "parent": parent, "world": wname, "lat": lat})
        print(f"[rreason]: gen {champ['gen']:3d} ({bop}) "
              f"{'PROMOTED ' if kept else 'discarded'} "
              f"score {best:.3f} best {parent:.3f} on '{wname}' {lat}s")


def mode_eval(path):
    g = json.load(open(path, encoding="utf-8"))
    s, world = _strategy_score(g)
    print(json.dumps({"score": s, "world": world, "gen": g.get("gen", 0)}))


def mode_status():
    g = _load_genome()
    s, world = _strategy_score(g)
    proms, cyc, tries = 0, 0, 0
    line = []
    try:
        for ln in open(LEDGER, encoding="utf-8-sig"):
            r = json.loads(ln)
            ev = r.get("ev")
            cyc += ev in ("WAKE", "PROMOTE", "DISCARD")
            tries += ev == "TRIED"
            proms += ev == "PROMOTE"
            if ev in ("WAKE", "PROMOTE"):
                line.append((r["ts"], r["gen"], r["parent"], r.get("op")))
    except Exception:
        pass
    print(f"[rreason]: gen {g['gen']} | strategy {g} | arena '{world}' "
          f"| score {s}")
    print(f"[rreason]: {cyc} cycles | {tries} tried | {proms} promotions")
    for ts, gn, fit, op in line[-5:]:
        print(f"    {ts} gen {gn:3d} score {fit} ({op})")


def mode_rollback(k=1):
    g = _load_genome()
    for _ in range(max(1, k)):
        pth = os.path.join(POOL, f"gen_{g['gen'] - 1}.json")
        if not os.path.exists(pth):
            print("[rreason]: no deeper checkpoint")
            return
        g = json.load(open(pth, encoding="utf-8"))
    _etch(g)
    print(f"[rreason]: heredity back to generation {g['gen']}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    m = a[0].lower()
    if m == "run":
        mode_run(int(a[1]) if len(a) > 1 else 20,
                 int(os.environ.get("RREASON_BUDGET_S", "1800")))
    elif m == "eval":
        mode_eval(a[1])
    elif m == "status":
        mode_status()
    elif m == "rollback":
        mode_rollback(int(a[1]) if len(a) > 1 else 1)
    elif m == "stop":
        with open(STOPF, "w") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
        print("[rreason]: stop-stone etched")
    else:
        print(__doc__)
