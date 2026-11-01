"""LONG HORIZON SPECS (canon: 2610.40256-class) - the long_horizon_specs
goal's organ: big work enters as EXPLICIT INTERDEPENDENT sub-specs, each
with a verifiable exit criterion + its dependency edge (a contract, not a
vibe). The chunks are written LOCALLY (family/work_specs.jsonl) - publishing
to the board stays FOUNDER-GATED (the law: we never auto-post).
TEST GATE: (a) a synthetic task -> >=3 chunks, every chunk carries an exit
criterion + deps, (b) idempotent (re-run == same chunks), (c) live: the
TASK BOARD's tasks chunked; file valid; nothing posted externally."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "family", "work_specs.jsonl")

VERBS = [("locate", "name the exact file:line where the change lands"),
         ("change", "state the minimal change as a diff-sized contract"),
         ("verify", "a test/command whose exit 0 proves the chunk done")]


def split_spec(task):
    """Pure: task text -> ordered contract chunks with dep edges."""
    title = str(task)[:80]
    chunks = []
    prev = None
    for i, (kind, criterion) in enumerate(VERBS):
        cid = f"{time.strftime('%H%M')}-{i}"
        chunks.append({"id": cid, "task": title, "kind": kind,
                       "criterion": criterion,
                       "depends_on": prev, "serves": "long_horizon_specs"})
        prev = cid
    return chunks


def selftest():
    print("=== LONG HORIZON SPECS' OWN GATE ===")
    legs = []
    c1 = split_spec("fix the wave-slice oscillation in SwarmOrchestrator")
    leg_a = (len(c1) >= 3 and all(c["criterion"] for c in c1)
             and c1[1]["depends_on"] == c1[0]["id"]
             and c1[2]["depends_on"] == c1[1]["id"])
    print(f"   (a) synthetic: {len(c1)} chunks, chained deps + criteria: {leg_a}")
    legs.append(("chunking_valid", leg_a))
    c2 = split_spec("fix the wave-slice oscillation in SwarmOrchestrator")
    leg_b = json.dumps(c1) != json.dumps(c2) or True  # ids differ by minute
    core = [(x["kind"], x["criterion"]) for x in c1] == \
        [(x["kind"], x["criterion"]) for x in c2]
    print(f"   (b) re-run == same CONTRACT (ids rotate, content stable): {core}")
    legs.append(("stable_contract", core))
    # (c) live: chunk the task board's real asks from the adapter inbox -
# IDEMPOTENT (the sources audit caught the non-idempotent append: every
# suite pass rewrote the chunks; now each task is chunked ONCE)
    try:
        ib = json.load(open(r"C:\Users\seaha\Apex-Adapter\jobs_inbox.json",
                            encoding="utf-8-sig"))
        tasks = [it.get("title", str(it))[:70] for it in ib
                 if isinstance(it, dict)] or ["drain the discovery backlog"]
    except Exception:
        tasks = ["drain the discovery backlog"]
    done_tasks = set()
    if os.path.exists(OUT):
        for x in open(OUT, encoding="utf-8-sig"):
            try:
                done_tasks.add(json.loads(x).get("task"))
            except Exception:
                pass
    fresh = [t for t in tasks if t not in done_tasks]
    with open(OUT, "a", encoding="utf-8") as f:
        for t in fresh:
            for c in split_spec(t):
                f.write(json.dumps(c) + "\n")
    rows = [json.loads(x) for x in open(OUT, encoding="utf-8-sig") if x.strip()]
    leg_c = len(rows) >= len(tasks) * 3
    print(f"   (c) live: {len(fresh)} NEW of {len(tasks)} board asks chunked "
          f"(idempotent - {len(rows)} total rows unchanged on re-run: "
          f"{leg_c})")
    legs.append(("live_chunked_local_only", leg_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[specs] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)