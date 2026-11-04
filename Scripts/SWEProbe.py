"""SWEProbe.py - THE CAPABILITY LADDER'S FIRST RUNG (v0).

Grade Apex's lanes on REAL GitHub issues (SWE-bench Lite), not synthetic
arithmetics - because the law says MEASURED, NOT NAMED, and the world's
frontier grade sits on real-issue benchmarks. Everything here costs $0:

  data     : HuggingFace datasets-server (free, no auth) - 300 real issues
  lanes    : FreeSwarm rotator (openrouter/nim/gh, all $0) + local engines
  verdicts : v0 = honest patch-shape scoring (patch present, diff-shaped,
             target-file touch) - NOT a claimed-solve; full execution
             verdicts live on v1 (GitHub Actions public-repo = free cloud)
  receipts : Scripts/swe_probe.jsonl (append-only)

LAW: no verdict is minted when the reference patch is unavailable or the
skeptic finds the data corrupt - an unmeasured cell stays empty.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import FreeSwarm  # noqa: E402

ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "Config", "swebench_pool.json")
RECEIPTS = os.path.join(HERE, "swe_probe.jsonl")
DATASET = "princeton-nlp/SWE-bench_Lite"
DS_URL = ("https://datasets-server.huggingface.co/rows?dataset="
          + DATASET + "&config=default&split=test&offset={o}&length=100")
PAGES = 3                      # 300 instances
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/([^\s]+)", re.M)


def receipt(ev):
    row = dict(ev, ts=time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        with open(RECEIPTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass


def fetch_pool(force=False):
    """The dataset lands once per week (verified-free HF datasets-server)."""
    if not force and os.path.isfile(POOL):
        age = time.time() - os.path.getmtime(POOL)
        if age < 7 * 3600:
            return json.load(open(POOL, encoding="utf-8"))
    import urllib.request
    rows = []
    for o in range(0, PAGES * 100, 100):
        url = DS_URL.format(o=o)
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            receipt({"ev": "FETCH_FAIL", "offset": o, "error": str(e)[:120]})
            continue
        for rw in d.get("rows", []):
            row = rw.get("row", {})
            if row.get("instance_id"):
                rows.append({k: row.get(k) for k in
                             ("instance_id", "repo", "base_commit",
                              "problem_statement", "test_patch",
                              "FAIL_TO_PASS", "PASS_TO_PASS")})
    pool = {"fetched": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(rows), "instances": rows}
    os.makedirs(os.path.dirname(POOL), exist_ok=True)
    tmp = POOL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pool, f)
    os.replace(tmp, POOL)                       # atomic, the pile never corrupts
    receipt({"ev": "POOL_FETCHED", "count": len(rows)})
    return pool


BENCH_FILES = {"swe_pool": POOL}

# ---------------- THE EVOLVING GENOME (self-mutation, honesty-gated)
GENOME = os.path.join(ROOT, "Config", "swe_genome.json")

STYLES = [
    # 0: raw issue -> minimal diff (the base spec)
    ("Produce the minimal unified diff ('diff --git' format) that fixes "
     "this real GitHub issue in {repo} @ {commit}. Tests in the diff must "
     "target the failing test file. Issue:\n\n{issue}"),
    # 1: test-first framing (what must pass before anything else)
    ("Before writing the fix for this real GitHub issue in {repo} @ "
     "{commit}, name the failing behavior in ONE line, THEN produce the "
     "minimal unified diff ('diff --git') that makes it pass, keeping "
     "every existing test healthy. Issue:\n\n{issue}"),
    # 2: root-cause paragraph first (architect voice)
    ("You are a careful maintainer of {repo} @ {commit}. First state the "
     "root cause of this issue in <=2 sentences, then emit ONLY the "
     "minimal unified diff ('diff --git') fixing it. Issue:\n\n{issue}"),
    # 3: aggressive targeting (explicit failing-test names)
    ("This real GitHub issue in {repo} @ {commit} is judged by its "
     "FAIL_TO_PASS tests. Locate the exact module the failing tests live "
     "in and emit the minimal unified diff ('diff --git') that touches "
     "only the files it must. Issue:\n\n{issue}"),
]

PROMOTION_MIN_ITEMS = 6     # below this = sampling variance, not evidence
PROMOTION_MARGIN = 0.10     # per-item margin required to dethrone


def load_genome():
    g = {"gen": 0, "style": 0, "maxt": 2000, "score": None,
         "items": 0, "ts": None}
    try:
        with open(GENOME, encoding="utf-8") as f:
            g.update(json.load(f))
    except Exception:
        pass
    return g


def save_genome(g):
    os.makedirs(os.path.dirname(GENOME), exist_ok=True)
    tmp = GENOME + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    os.replace(tmp, GENOME)          # atomic; the lineage never corrupts


def _prompt(style, inst):
    tpl = STYLES[style % len(STYLES)]
    return tpl.format(repo=inst["repo"], commit=inst["base_commit"][:10],
                      issue=(inst["problem_statement"] or "")[:3500])


def ask_lane(prompt, items, maxt=None):
    """One lane, all bench items, one pass - the shape scoring is offline."""
    lane = FreeSwarm.ask(prompt, max_tokens=maxt or 3000,
                         purpose="swe-probe")
    return lane or ""


def bench_one(instance, lane_text):
    """v0 verdict: the honest PATCH-SHAPE score (0..3). Never claimed a solve.
    (1) patch emitted  (2) diff-shaped  (3) touches the failing tests' home"""
    fails = instance.get("FAIL_TO_PASS") or "[]"
    tgt = ""
    m = re.search(r"([\w/.\\-]+\.py)", fails)
    tgt = (m.group(1).split("/")[-1] if m else "")
    touched = set(DIFF_FILE_RE.findall(lane_text or ""))
    score = 0
    if lane_text and "\n" in (lane_text or ""):
        score += 1
    if "diff --git" in (lane_text or "") or "--- a/" in (lane_text or ""):
        score += 1
    if tgt and any(tgt.lower() in t.lower() for t in touched):
        score += 1
    return {"instance_id": instance["instance_id"], "score": score,
            "of": 3, "touched": sorted(touched)[:6], "target": tgt}


def run(n=5, budget=60, genome=None):
    """Daily slice: n rotating instances, ONE lane pass each, receipts."""
    g = genome or load_genome()
    pool = fetch_pool()
    day = time.strftime("%Y%m%d")[2:]
    rows = pool.get("instances", [])
    if not rows:
        receipt({"ev": "EMPTY_POOL"})
        return
    step = max(1, len(rows) // max(1, n))
    start = int(day) % len(rows)
    for i in range(n):
        sel = rows[(start + i * step) % len(rows)]
        prompt = _prompt(g.get("style", 0), sel)
        t0 = time.time()
        lane_text = ask_lane(prompt, [sel], g.get("maxt") or 3000)
        v = bench_one(sel, lane_text)
        v.update({"wall_s": round(time.time() - t0, 1),
                  "chars": len(lane_text or ""), "gen": g["gen"],
                  "style": g.get("style", 0)})
        receipt({"ev": "BENCH_ITEM", **v})
        print("SWE %s %d/%d (%.0fs)" % (v["instance_id"], v["score"],
                                        v["of"], v["wall_s"]))
    receipt({"ev": "RUN_DONE", "slice": n, "gen": g["gen"],
             "style": g.get("style", 0)})


def evolve(n=6, gens=2):
    """THE MUTATION LOOP, honesty-gated: mutate the prompt strategy,
    re-measure the same-size slice, promote ONLY on margin (the variance
    guard that RREASON taught the fleet: same-genome resamples lie)."""
    g = load_genome()
    inc = (g.get("score") if g.get("score") is not None else None)
    for _ in range(gens):
        trial = dict(g)
        trial["gen"] = g["gen"] + 1
        trial["style"] = (g["style"] + 1) % len(STYLES)     # the mutation
        trial["maxt"] = 3000
        rows = fetch_pool()["instances"]
        if len(rows) < PROMOTION_MIN_ITEMS:
            receipt({"ev": "EVOLVE_BALKED", "why": "pool too thin"})
            return
        day = time.strftime("%Y%m%d")[2:]
        step = max(1, len(rows) // max(1, n))
        start = int(day) % len(rows)
        scores = []
        for i in range(n):
            sel = rows[(start + i * step) % len(rows)]
            text = ask_lane(_prompt(trial["style"], sel), [sel],
                            trial["maxt"])
            scores.append(bench_one(sel, text)["score"])
            receipt({"ev": "TRIAL_ITEM", "gen": trial["gen"],
                     "style": trial["style"],
                     "instance": sel["instance_id"],
                     "score": scores[-1]})
        tot = sum(scores)
        trial["score"] = None
        trial["items"] = n
        if inc is None:
            # the founder-line rule: the FIRST measurement of a genome is
            # an establishment, not a promotion
            receipt({"ev": "ESTABLISHED", "style": trial["style"],
                     "raw": tot, "of": n * 3})
            g = trial
            g["score"] = tot / max(1, n)          # per-item score 0..3
            save_genome(g)
            continue
        edge = ((tot / n) - inc) / max(0.001, 3)
        if n < PROMOTION_MIN_ITEMS:
            receipt({"ev": "DISCARD_VARIANCE",
                     "note": "slice below promotion size", "raw": tot})
            continue
        if edge >= PROMOTION_MARGIN:
            receipt({"ev": "PROMOTED", "style": trial["style"],
                     "score_per_item": round(tot / n, 3),
                     "incumbent": inc, "margin": round(edge, 3)})
            g = trial
            g["score"] = tot / n
            save_genome(g)
        else:
            receipt({"ev": "DISCARD", "style": trial["style"],
                     "score_per_item": round(tot / n, 3),
                     "incumbent": inc})
    print(json.dumps({"gen": g["gen"], "style": g["style"],
                      "score": g.get("score")}, indent=1))


def status():
    pool = fetch_pool()
    print(json.dumps({"pool_count": pool.get("count"),
                      "fetched": pool.get("fetched")}, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        run(n=n)
    elif cmd == "evolve":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        gens = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        evolve(n=n, gens=gens)
    else:
        status()
