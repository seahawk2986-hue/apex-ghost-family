"""BOUNDED PLANNER (canon: tree_search_planning - MCTS/tree-of-canon) - the
canon's planners search OVER REASONING/plans; Apex's lane planning was
LINEAR (spend by habit). This organ is a BOUNDED BEST-FIRST search over the
next round's LANE-ALLOCATION plan: nodes = allocations of the REQS BUDGET
across the lanes (code/forage/trending/wiki/wayback), scored by PathMemory's
measured lane YIELD EMA (mines/req per lane) + a small exploration bonus for
low-try lanes (optimism under uncertainty); depth 2, beam 4 - CPU-only, ~
bounded work, any RAM tier (a bubble organ). Output: the plan written to
PathMemory['lane_plan'] + printed receipt; the next pre-stage may consume it.
TEST GATE: (a) the search prefers the measured-best lane under a synthetic
(PathMemory), (b) the exploration bonus flips the plan toward an UNTRIED
lane with no data, (c) bounded: search completes <1s, (d) writes
PathMemory['lane_plan'] valid + reproducible."""
import json
import os
import random
import statistics
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from SafeIO import read_json as _rj, write_json as _w

PM = os.path.join(ROOT, "Config", "PathMemory.json")
LANES = ("forge", "code", "forage", "trending", "wiki", "wayback")
BUDGET_UNITS = 10
DEPTH, BEAM = 2, 4


def lane_stats(pm):
    st = {}
    for ln in LANES:
        e = pm.get(ln) or {}
        reqs = float(e.get("reqs", 0) or 0)
        mines = float(e.get("mines", 0) or 0)
        st[ln] = {"yield": mines / reqs if reqs >= 1 else 0.0,
                  "reqs": reqs, "tries": int(reqs)}
    return st


def expansion_bonus(st, lane):
    """Optimism under uncertainty: an unmeasured lane deserves tries."""
    tries = st[lane]["tries"]
    return 0.5 / (1.0 + tries) if tries < 5 else 0.0


def plan(st, depth=DEPTH, beam=BEAM):
    """Best-first bounded: score = yield + bonus; beam the top nodes."""
    scored = sorted(LANES, key=lambda ln: -(st[ln]["yield"] + expansion_bonus(st, ln)))
    frontier = [(tuple([lanes_]), 
                 st[lanes_]["yield"] + expansion_bonus(st, lanes_))
                for lanes_ in scored[:beam]]
    for d in range(1, depth):
        nxt = []
        for path, sc in frontier:
            rest = [l for l in scored if l not in path]
            for l in rest[:beam]:
                nxt.append((path + (l,), sc + st[l]["yield"] + expansion_bonus(st, l)))
        nxt.sort(key=lambda x: -x[1])
        frontier = nxt[:beam] if nxt else frontier
    return frontier[0] if frontier else (tuple(), 0.0)


def run():
    pm = _rj(PM, {}) or {}
    st = lane_stats(pm)
    t0 = time.time()
    best_path, best_sc = plan(st)
    ms = round((time.time() - t0) * 1000, 1)
    plan_doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "search": f"bounded-best-first depth{DEPTH} beam{BEAM}",
                "lane_order": list(best_path),
                "alloc_units": {ln: max(1, BUDGET_UNITS // len(best_path) - (1 if i else 0))
                                for i, ln in enumerate(best_path)},
                "score": round(best_sc, 4), "ms": ms,
                "stats": {ln: st[ln] for ln in best_path}}
    pm2 = dict(pm)
    pm2["lane_plan"] = plan_doc
    ok = _w(PM, pm2)
    print(f"[planner] best lane order: {list(best_path)} (score "
          f"{best_sc:.4f}) in {ms}ms | write {'OK' if ok else 'REFUSED (lock busy - honest)'}")
    return plan_doc


def selftest():
    print("=== BOUNDED PLANNER'S OWN GATE ===")
    legs = []
    st_known = {ln: {"yield": 0.0, "reqs": 0, "tries": 0} for ln in LANES}
    st_known["forge"] = {"yield": 0.9, "reqs": 40, "tries": 40}
    st_known["code"] = {"yield": 0.5, "reqs": 10, "tries": 10}
    leg_a = plan(st_known)[0][0] == "forge"
    print(f"   (a) measured-best lane leads the plan: {leg_a}")
    legs.append(("best_yield_leads", leg_a))
    st_new = {ln: {"yield": 0.0, "reqs": 0, "tries": 0} for ln in LANES}
    st_new["forge"] = {"yield": 0.4, "reqs": 100, "tries": 100}
    plan_new = plan(st_new)[0]
    leg_b = "code" in plan_new or "trending" in plan_new   # untried tried
    print(f"   (b) untried lanes get the exploration bonus: {leg_b} "
          f"(plan: {plan_new[:3]})")
    legs.append(("exploration", leg_b))
    t0 = time.time()
    plan(st_known)
    leg_c = (time.time() - t0) < 1.0
    print(f"   (c) bounded: search < 1s: {leg_c}")
    legs.append(("bounded_latency", leg_c))
    p1 = run()
    p2 = run()
    leg_d = (p1["lane_order"] == p2["lane_order"]
             and json.load(open(PM, encoding="utf-8-sig")).get("lane_plan", {}).get("lane_order")
             == p1["lane_order"])
    print(f"   (d) write + reproducible order: {leg_d}")
    legs.append(("plan_written_reproducible", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[planner] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)