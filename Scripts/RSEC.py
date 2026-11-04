"""RSEC - THE RECURSIVE SELF-EVOLUTIONARY CORE Population Edition
(single file; $0; stdlib only; no network inside the evolution loop;
2026-11-03):

  BIRTH      a first 'run' autogenes the seed genome beside itself.
             The file is everything: code = constitution, genome =
             heredity (rsec_genome.json).
  SPEED      each cycle breeds a POPULATION of children (RSEC_POP,
             default 4) evaluated CONCURRENTLY by fresh subprocess
             mirrors of this core; the tournament's champion is the
             only candidate promotion ever sees - the wall-clock
             evolution rate scales with lanes that stay free forever.
  OUTSOURCE  Config-relative tasks_inbox/*.json ({name, xs, ys}) can be
             dropped by ANY free external source (a swarm organ, a SCM
             hunter, a human) and becomes the fitness world; when the
             inbox is empty the builtin bench runs - the loop never
             starves (this is the only honest meaning of 'forever').
  BANDIT     the mutator reads its OWN earned promotion statistics from
             the append-only receipt ledger and re-budgets its op-
             choices toward what wins. The ledger teaches; only a
             promotion ever touches the heredity.
  LAWS       1. every child receipts; nothing minted
             2. no network, no keys, $0 forever
             3. an RSEC_STOP file beside me halts between cycles
             4. every promotion checkpoints rsec_pool/ - rollback <1s
             5. eval timeout 45s + node cap 64: runaway genomes starve
                themselves, never the host
             6. promotion ONLY on child-beats-parent (tournament-blind)
             7. the ledger is append-only; status prints stalls + deaths

  CLI:  python RSEC.py run [cycles]    - autonomous loop (population)
        python RSEC.py eval <g.json>   - score a genome (the child mode)
        python RSEC.py status          - the honest ledger read
        python RSEC.py rollback [k]    - step heredity back k gens
        python RSEC.py stop            - etch the stop-stone (law 3)"""
import concurrent.futures
import copy
import json
import math
import os
import random
import subprocess
import sys
import time

HOME = os.environ.get("RSEC_HOME") or os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HOME, "rsec_receipts.jsonl")
POOL = os.path.join(HOME, "rsec_pool")
STOPF = os.path.join(HOME, "RSEC_STOP")
GENOME_F = os.path.join(HOME, "rsec_genome.json")
INBOX = os.path.join(HOME, "tasks_inbox")

BI_OPS = ("add", "sub", "mul", "sdiv", "min", "max")
UN_OPS = ("sin", "tanh", "abs", "neg", "cap", "sq", "root")
XGRID = [round(-2 + 4 * i / 32, 6) for i in range(33)]
POP = max(2, int(os.environ.get("RSEC_POP", "4")))


def _target(x):
    return (0.65 * math.sin(1.9 * x) + 0.30 * (abs(x) ** 0.9)
            * math.tanh(1.1 * x) + 0.12)


def _inbox_task():
    """THE OUTSOURCE DOOR: the newest VALID world in the inbox wins;
    anything malformed is skipped loudly-but-blamelessly; empty inbox =
    the builtin world (the loop never starves)."""
    try:
        files = sorted(f for f in os.listdir(INBOX) if f.endswith(".json"))
    except Exception:
        return ("builtin", None)
    for fn in reversed(files):
        try:
            t = json.load(open(os.path.join(INBOX, fn), encoding="utf-8"))
            xs, ys = t["xs"], t["ys"]
            if (isinstance(xs, list) and isinstance(ys, list)
                    and len(xs) == len(ys) and 8 <= len(xs) <= 256
                    and all(isinstance(v, (int, float)) for v in xs + ys)
                    and all(abs(v) < 1e6 for v in xs + ys)):
                return (str(t.get("name") or fn)[:60], (xs, ys))
        except Exception:
            continue
    return ("builtin", None)


def _task():
    return _inbox_task()


def _ev(n, x, d=0):
    if not isinstance(n, list) or d > 40:
        return 0.0
    o = n[0]
    if o == "x":
        return x
    if o == "c":
        try:
            return max(-9.0, min(9.0, float(n[1])))
        except Exception:
            return 0.0
    a = _ev(n[1], x, d + 1)
    if o in BI_OPS:
        b = _ev(n[2] if len(n) > 2 else 0.0, x, d + 1)
        if o == "add":
            return a + b
        if o == "sub":
            return a - b
        if o == "mul":
            return max(-9.0, min(9.0, a * b))
        if o == "sdiv":
            return (a / b) if abs(b) > 1e-9 else 0.0
        return min(a, b) if o == "min" else max(a, b)
    if o == "sin":
        return math.sin(a)
    if o == "tanh":
        return math.tanh(max(-9.0, min(9.0, a)))
    if o == "abs":
        return abs(a)
    if o == "neg":
        return -a
    if o == "cap":
        return max(-1.618, min(1.618, a))
    if o == "sq":
        return max(-9.0, min(9.0, a * a))
    if o == "root":
        return math.sqrt(abs(a))
    return 0.0


def _count(n):
    if not isinstance(n, list) or len(n) < 2:
        return 1
    return 1 + sum(_count(c) for c in n[1:])


def _score(g):
    """THE FITNESS: world = newest inbox task or the builtin bench; the
    parsimony tax keeps fitting AND staying small (law 5's sibling)."""
    name, world = _task()
    xs, ys = world if world else (XGRID, [_target(x) for x in XGRID])
    t = g["tree"]
    if _count(t) > 64:
        return 1e9
    mse = sum((_ev(t, x) - y) ** 2 for x, y in zip(xs, ys)) / max(1, len(xs))
    return mse + 0.0022 * _count(t)


def _gather(tree):
    out = [(None, None, tree)]
    def step(n):
        if isinstance(n, list):
            for j, c in enumerate(n):
                if j == 0 or not isinstance(c, list):
                    continue   # op-strings and float payloads are NOT spots
                out.append((n, j, c))
                step(c)
    step(tree)
    return out


def _rand_tree(rng, ops, d=0):
    if d >= 3 or (d > 0 and rng.random() < 0.5):
        return ["x"] if rng.random() < 0.4 else ["c",
                                                 round(rng.uniform(-2, 2), 4)]
    if rng.random() < 0.35:
        return [rng.choice(ops["un"]), _rand_tree(rng, ops, d + 1)]
    return [rng.choice(ops["bi"]), _rand_tree(rng, ops, d + 1),
            _rand_tree(rng, ops, d + 1)]


def _bandit():
    """THE LEDGER TEACHES: per-op promotion rates over the recent
    window; unseen ops keep their base weight (the young get a chance).
    Returns weights for (jit, swap, graft, prune, meta)."""
    w = [0.30, 0.18, 0.24, 0.12, 0.16]
    tally = {}
    try:
        rows = [json.loads(l) for l in
                open(LEDGER, encoding="utf-8-sig")][-400:]
    except Exception:
        return w
    for r in rows:
        if r.get("ev") in ("PROMOTE", "DISCARD"):
            op = r.get("op", "jit")
            t = tally.setdefault(op, [0, 0])
            t[0 if r["ev"] == "PROMOTE" else 1] += 1
    for i, op in enumerate(("jit", "swap", "graft", "prune")):
        t = tally.get(op)
        if t and t[0] + t[1] >= 4:
            w[i] *= (0.4 + 1.2 * t[0] / (t[0] + t[1])) / 1.0
    return w


def _mutate(g, rng, w):
    child = copy.deepcopy(g)
    ops = child["ops"]
    tree = child["tree"]
    rate = max(0.05, min(0.85, child.get("rate", 0.35)))
    kind = rng.choices(("jit", "swap", "graft", "prune", "meta"),
                       weights=w)[0]
    if kind == "jit":                                # JITTER a constant
        _, _, hit = rng.choice(_gather(tree))
        if (isinstance(hit, list) and hit[0] == "c"
                and isinstance(hit[1], (int, float))):
            hit[1] = round(hit[1] + rng.gauss(0, 0.35) * (1 + rate), 4)
        else:
            tree = ["add", tree, ["c", round(rng.gauss(0, 0.2), 4)]]
    elif kind == "swap":                             # SWAP an operator
        _, _, hit = rng.choice(_gather(tree))
        if isinstance(hit, list):
            pool = ops["un"] + ops["bi"]
            if hit[0] in pool:
                hit[0] = rng.choice([o for o in pool if o != hit[0]])
    elif kind == "graft":                            # GRAFT fresh subtree
        p, i, _ = rng.choice(_gather(tree))
        if p is None:
            tree = _rand_tree(rng, ops, d=1)
        else:
            p[i] = _rand_tree(rng, ops, d=1)
    elif kind == "prune":                            # PRUNE to constant
        p, i, _ = rng.choice(_gather(tree))
        tree = _graft_c(tree, p, i)
    else:                                            # the META-channel
        child["rate"] = round(rng.uniform(0.05, 0.7), 3)
    child["tree"] = tree
    child["gen"] = g.get("gen", 0) + 1
    return child, kind


def _graft_c(tree, parent, idx):
    const = ["c", round(random.uniform(-2, 2), 4)]
    if parent is None:
        return const
    parent[idx] = const
    return tree


def _seed():
    rng = random.Random(17935)
    ops = {"bi": list(BI_OPS), "un": list(UN_OPS)}
    return {"gen": 0, "rate": 0.35, "ops": ops,
            "tree": _rand_tree(rng, ops, 1)}


def _etch(g):
    tmp = GENOME_F + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    os.replace(tmp, GENOME_F)                        # the atomic etch


def _load_genome():
    try:
        g = json.load(open(GENOME_F, encoding="utf-8"))
        if not isinstance(g, dict) or "tree" not in g:
            raise ValueError("malformed heredity")
        return g
    except Exception:
        g = _seed()
        _etch(g)
        return g


def _receipt(row):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _child_eval(path, timeout=45):
    """THE RECURSIVE MIRROR: a subprocess of this core scores a copy of
    itself; the child's death stays in the mirror (law 5)."""
    try:
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "eval", path], capture_output=True, text=True,
                           timeout=timeout)
        return json.loads(r.stdout.strip().splitlines()[-1])["score"]
    except Exception:
        return None


def mode_run(cycles=50, budget_s=900, eps=1e-7):
    os.makedirs(POOL, exist_ok=True)
    tname, _ = _task()
    g = _load_genome()
    parent = _score(g)
    _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ev": "WAKE",
              "gen": g["gen"], "parent": round(parent, 6), "task": tname})
    print(f"[rsec]: waking at gen {g['gen']} | fitness {parent:.5f} | "
          f"world '{tname}' | pop {POP}")
    t_end = time.time() + budget_s
    for _ in range(cycles):
        if os.path.exists(STOPF):                    # law 3
            print("[rsec]: the stop-stone stands - halted between cycles")
            break
        if time.time() >= t_end:                     # law 5
            print("[rsec]: the time budget closes the loop")
            break
        t0 = time.time()
        w = _bandit()
        kids = [_mutate(g, random.Random(), w) for _ in range(POP)]
        paths = []
        for kid, _k in kids:
            p = os.path.join(POOL, f"cand_{os.getpid()}_"
                             f"{random.randint(1_000_000, 9_000_000)}.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(kid, f)
            paths.append(p)
        with concurrent.futures.ThreadPoolExecutor(max_workers=POP) as ex:
            scores = list(ex.map(_child_eval, paths))
        lat = round(time.time() - t0, 3)
        for (kid, kind), p, sc in zip(kids, paths, scores):
            try:
                os.remove(p)
            except Exception:
                pass
            _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ev":
                      "TRIED", "gen": kid["gen"], "op": kind,
                      "child": round(sc, 6) if sc is not None else None,
                      "lat": lat})
        ranked = sorted(((sc, kid, kind) for (sc, (kid, kind))
                         in zip(scores, kids)
                         if sc is not None), key=lambda r: r[0])
        if not ranked:
            print(f"[rsec]: the whole brood died in the mirror "
                  f"(the lineage outlives it)")
            continue
        cs, champ, op = ranked[0]
        kept = cs < parent - eps                     # law 6
        if kept:
            g = champ
            parent = cs
            _etch(g)
            with open(os.path.join(POOL, f"gen_{g['gen']}.json"), "w",
                      encoding="utf-8") as f:
                json.dump(g, f, indent=1)
        _receipt({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "ev": "PROMOTE" if kept else "DISCARD", "gen":
                  champ["gen"], "op": op, "child": round(cs, 6),
                  "parent": round(parent, 6), "task": tname, "lat": lat})
        print(f"[rsec]: gen {champ['gen']:3d} ({op}) "
              f"{'PROMOTED ' if kept else 'discarded'} "
              f"score {cs:.5f} best {parent:.5f} {lat}s pop{POP}")


def mode_eval(path):
    g = json.load(open(path, encoding="utf-8"))
    print(json.dumps({"score": round(_score(g), 6), "gen": g.get("gen", 0)}))


def mode_status():
    g = _load_genome()
    s = _score(g)
    tname, _ = _task()
    proms, dies, cyc, tries = 0, 0, 0, 0
    line = []
    try:
        for ln in open(LEDGER, encoding="utf-8-sig"):
            r = json.loads(ln)
            ev = r.get("ev")
            cyc += ev in ("WAKE", "PROMOTE", "DISCARD", "DIED")
            tries += ev == "TRIED"
            proms += ev == "PROMOTE"
            dies += ev == "DIED"
            if ev in ("WAKE", "PROMOTE"):
                line.append((r["ts"], r["gen"], r["parent"], r.get("op")))
    except Exception:
        pass
    print(f"[rsec]: generation {g['gen']} | meta-rate {g['rate']} | "
          f"nodes {_count(g['tree'])} | fitness {s:.6f} | world '{tname}'")
    print(f"[rsec]: {cyc} cycles | {tries} children tried | "
          f"{proms} promotions | {dies} deaths | lineage (newest 5):")
    for ts, gn, fit, op in line[-5:]:
        print(f"    {ts} gen {gn:3d} fit {fit} ({op})")


def mode_rollback(k=1):
    g = _load_genome()
    for _ in range(max(1, k)):
        pth = os.path.join(POOL, f"gen_{g['gen'] - 1}.json")
        if not os.path.exists(pth):
            print("[rsec]: no deeper checkpoint - heredity holds")
            return
        g = json.load(open(pth, encoding="utf-8"))
    _etch(g)
    print(f"[rsec]: heredity stepped back to generation {g['gen']}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    m = a[0].lower()
    if m == "run":
        mode_run(int(a[1]) if len(a) > 1 else 50,
                 int(os.environ.get("RSEC_BUDGET_S", "900")))
    elif m == "eval":
        mode_eval(a[1])
    elif m == "status":
        mode_status()
    elif m == "rollback":
        mode_rollback(int(a[1]) if len(a) > 1 else 1)
    elif m == "stop":
        with open(STOPF, "w") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
        print("[rsec]: the stop-stone etched - the next cycle halts")
    else:
        print(__doc__)
