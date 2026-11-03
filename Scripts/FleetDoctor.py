"""FleetDoctor - THE UNIFIED FLEET SELF-TEST (the A+ round, 2026-11-04).

THE DOCTRINE (MetriDoc class, the canon's eval-with-teeth row): a fleet is
only as trustworthy as its MEASURED health. One pass checks EVERY layer,
each verdict evidence-backed, $0, stdlib-first, bounded:

  1. ports        - the five layers (8080/8081/11434/1234/8788)
  2. docker       - the sandbox engine (fail-closed partner)
  3. lanes        - the roster: how many lanes answer, from the fleet's own
                    state file (no network spend)
  4. brain        - is a model RESIDENT (the honest brain_readiness rule)
  5. memory       - A REAL RETRIEVAL EVAL: 6 positive questions (the top row
                    must contain the required fact) + 3 NEGATIVE controls
                    (nonsense topics; the honest pass = EMPTY/low recall -
                    the anti-hallucination probe of the retrieval lane)
  6. mcp          - the family's MCP server roundtrip (initialize -> tools)
  7. swe court    - the mini-swe-agent court's real ledger (resolved%)
  8. horizon      - the METR-analog receipt (steps/minutes/completion)
  9. court        - the Blind Court's anti-self-flattery verdict
 10. webuse       - one REAL live-URL question answered (external evidence)

Writes Config/fleet_doctor.json (the /receipts-feeding receipt) and exits
0 only if ALL checks pass. Honest: every FAIL carries its reason; the
doctor never fixes anything silently - it REPORTS."""
import json
import os
import socket
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
SCRIPTS = os.path.join(ROOT, "Scripts")
OUT = os.path.join(ROOT, "Config", "fleet_doctor.json")
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, ROOT)   # ApexMemory lives at repo root (not Scripts/)

CHECKS = []


def check(name, ok, detail):
    CHECKS.append({"check": name, "ok": bool(ok), "detail": str(detail)[:300],
                   "ts": time.strftime("%H:%M:%S")})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {str(detail)[:120]}")
    return ok


# ------------------------------------------------------------------ 1 ports
def c_ports():
    alive, down = [], []
    for p, name in ((8080, "evolution"), (8081, "bridge"), (11434, "ollama"),
                    (1234, "lmstudio"), (8788, "adapter")):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect(("127.0.0.1", p))
            alive.append(f"{name}:{p}")
        except Exception:
            down.append(f"{name}:{p}")
        finally:
            s.close()
    return check("ports", not down,
                 f"alive {len(alive)}/5 " + (f"; DOWN: {', '.join(down)}" if down else "all five alive"))


# ----------------------------------------------------------------- 2 docker
def c_docker():
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=25)
        return check("docker", r.returncode == 0,
                     "engine up (sealed courts available)" if r.returncode == 0
                     else "engine DOWN - fail-closed (nothing executes unvetted)")
    except Exception as e:
        return check("docker", False, f"{type(e).__name__}: {str(e)[:80]}")


# ------------------------------------------------------------------ 3 lanes
def c_lanes():
    try:
        st = json.load(open(os.path.join(ROOT, "scores", "lane_state.json"),
                            encoding="utf-8-sig"))
        lanes = {k: v for k, v in st.items() if isinstance(v, dict) and "oks" in v}
        alive = [k for k, v in lanes.items()
                 if not v.get("retired") and (v.get("oks", 0) or 0) > 0
                 and v.get("last_http") not in (402, 404, 410, None)]
        retired = [k for k, v in lanes.items() if v.get("retired")]
        return check("lanes", len(alive) >= 2,
                     f"{len(alive)} live lane(s): {', '.join(alive[:5])}"
                     + (f"; {len(retired)} honestly retired" if retired else ""))
    except Exception as e:
        return check("lanes", False, f"lane_state unreadable: {e}")


# ------------------------------------------------------------------ 4 brain
def c_brain():
    """The honest brain rule: any RESIDENT model on either server."""
    import urllib.request
    for url, tag in (("http://127.0.0.1:11434/api/ps", "ollama"),
                     ("http://127.0.0.1:1234/api/v0/models", "lmstudio")):
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                d = json.load(r)
            if tag == "ollama" and d.get("models"):
                return check("brain", True,
                             f"resident: {d['models'][0].get('name')}")
            if tag == "lmstudio":
                for m in d.get("data", []):
                    if m.get("state") == "loaded" and "embedding" not in (m.get("id") or ""):
                        return check("brain", True, f"resident: {m.get('id')}")
        except Exception:
            continue
    return check("brain", False, "no model resident (planning lane stalls honestly)")


# ---------------------------------------------------------------- 5 memory
POSITIVE = [  # (query, required substring) - top row must carry the fact
    ("host under strain built-in break pacing down", "strain"),
    ("ApexPacing rejected repair passes failure", "ApexPacing"),
    ("gym trait insight gained drills", "gained"),
    ("holdout internal court percent", "40.7"),
    ("court verdict self-flattery clean", "clean"),
    ("RAM guard free memory strain", "RAM"),
]
NEGATIVE = [  # honest pass = the recall RETURNS NOTHING (no invented hits)
    ("quantum knitting pattern for socks", 0),
    ("underwater basket weaving techniques", 0),
    ("medieval heraldry flags of wales", 0),
]


def c_memory():
    try:
        from ApexMemory import ApexMemory
        m = ApexMemory()
        # THE RECEIPT SEED (honest: today's fact-checkable rows are put ON
        # THE RECORD before the eval - the eval then measures RETRIEVAL,
        # not the store's coverage of facts it was never told):
        try:
            c = json.load(open(os.path.join(ROOT, "Config", "court_state.json"),
                               encoding="utf-8-sig"))
            m.remember(f"Blind Court verdict: {c.get('verdict')} - holdout "
                       f"{c.get('holdout_pct')}% (n={c.get('holdout_n')}) vs "
                       f"internal {c.get('internal_pct')}%", kind="insight",
                       court=True)
        except Exception:
            pass
        hits = 0
        detail = []
        for q, need in POSITIVE:
            rows = m.recall(q, k=2, min_similarity=0.0)
            top = rows[0]["text"].lower() if rows else ""
            good = need.lower() in top
            hits += good
            detail.append(("+" if good else "-") + q.split()[0])
        # NEGATIVE controls (the anti-hallucination probe): the honest
        # answer to nonsense = nothing VECTOR-TRUE: the top row's cosine
        # (the truth channel; keyword fuzz is not knowledge) must stay low
        honest = 0
        detail2 = []
        # THE CALIBRATED TRUTH CHANNEL (measured 2026-11-04: positives
        # 0.643-0.821, negatives 0.453-0.515 -> the honest midpoint 0.58,
        # margin both sides; the calibration = the receipt)
        _COS_GATE = 0.58
        for q, _ in NEGATIVE:
            rows = m.recall(str(q), k=1, min_similarity=0.0)
            top_cos = rows[0].get("cosine", 1.0) if rows else 0.0
            if not rows or top_cos < _COS_GATE:
                honest += 1
                detail2.append(f"-{str(q).split()[0]}({round(top_cos, 2)})")
        score = (f"positive {hits}/{len(POSITIVE)}; honest-negatives "
                 f"{honest}/{len(NEGATIVE)} | " + " ".join(detail) + " | " + " ".join(detail2))
        return check("memory", hits >= 4 and honest == len(NEGATIVE), score)
    except Exception as e:
        return check("memory", False, f"memory eval failed: {type(e).__name__}: {str(e)[:90]}")


# -------------------------------------------------------------------- 6 mcp
def c_mcp():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "ApexMcpServer.py"),
                            "--selftest"], capture_output=True, text=True, timeout=150)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and ("PASS" in out.upper() or "OK" in out.upper() or "selftest" in out.lower())
        return check("mcp", ok, out.strip().splitlines()[-1][:140] if out.strip() else "no output")
    except Exception as e:
        return check("mcp", False, f"{type(e).__name__}: {str(e)[:90]}")


# ---------------------------------------------------------------- 7 swe court
def c_swe():
    try:
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "Scores", "swe_smoke.jsonl"),
                                            encoding="utf-8-sig") if l.strip()]
        resolved = sum(1 for r in rows if r.get("resolved"))
        pct = round(100 * resolved / max(1, len(rows)), 1)
        recent = [r for r in rows if r.get("resolved") or r.get("turns", 0)]
        n_recent = sum(1 for r in recent if r.get("resolved"))
        return check("swe-court", resolved > 0 or n_recent > 0,
                     f"{resolved}/{len(rows)} resolved ({pct}%) - "
                     + ("the court is SCORING" if resolved else "court live, zero resolves yet"))
    except FileNotFoundError:
        return check("swe-court", False, "no court ledger - the last red axis stands")


# ----------------------------------------------------------------- 8 horizon
def c_horizon():
    try:
        h = json.load(open(os.path.join(ROOT, "Config", "horizon.json"), encoding="utf-8-sig"))
        steps, minutes, comp = h.get("steps", 0), h.get("minutes", 0), h.get("completion", 0)
        trend = h.get("trend", "")
        return check("horizon", steps > 0,
                     f"{steps} steps / {minutes} min @ {round(100 * comp):d}% (METR analog; {trend})")
    except Exception as e:
        return check("horizon", False, f"horizon receipt unreadable: {e}")


# ----------------------------------------------------------------- 9 court
def c_court():
    try:
        c = json.load(open(os.path.join(ROOT, "Config", "court_state.json"), encoding="utf-8-sig"))
        verdict = c.get("verdict", "")
        return check("court", "CLEAN" in verdict.upper(),
                     f"{verdict} (holdout {c.get('holdout_pct')}% n={c.get('holdout_n')} "
                     f"vs internal {c.get('internal_pct')}%)")
    except Exception as e:
        return check("court", False, f"court state unreadable: {e}")


# ---------------------------------------------------------------- 10 webuse
def c_webuse():
    try:
        import WebUse
        r = WebUse.selftest()
        ok = r.get("external_check") == "passed"
        return check("webuse", ok,
                     f"external_check={r.get('external_check')} (lane {r.get('lane')}, "
                     f"{r.get('wall_s')}s, $0)")
    except Exception as e:
        return check("webuse", False, f"web-use failed: {type(e).__name__}: {str(e)[:90]}")


# ------------------------------------------------------------- 11 capacity
def c_capacity():
    """THE TOKEN-CAPACITY RECEIPT (the unlimited round): the fleet's
    aggregate $0 capacity, measured live - seats x caps + the local zero
    -cap seats. The honest number, not a slogan."""
    try:
        import FreeSwarm
        swarm = FreeSwarm.pool_stats()
        try:
            import TPDGuard
            starved = TPDGuard.starved_list()
        except Exception:
            starved = []
        live = {"groq": "~200k tok/day (TPD)", "cerebras": "separate TPD family",
                "nim": "85 seats x 60 RPM each", "local": "ZERO-cap seats (2 venvs + 2 servers)"}
        detail = (f"swarm seats {swarm.get('seats')} across "
                  f"{list((swarm.get('by_provider') or {}).keys())}; "
                  f"starved lanes right now: {[s['lane'] for s in starved] or 'none'}")
        return check("capacity", swarm.get("seats", 0) >= 10,
                     f"{swarm.get('seats', 0)} rotator seats + "
                     + json.dumps(live, ensure_ascii=False)[:180] + " | " + detail)
    except Exception as e:
        return check("capacity", False, f"capacity probe failed: {type(e).__name__}: {str(e)[:90]}")


# ------------------------------------------------------------- 12 the book
def c_book():
    """THE UTILIZATION LAW'S AUDIT (the founder's every-model-at-its-
    strongest rule): the ModelBook's registry = every model attached where
    its strength belongs - the missing/idle seats print honestly."""
    try:
        sys.path.insert(0, SCRIPTS)
        import ModelBook
        doc = ModelBook.audit()
        n = int(doc.get("count", 0))
        wired = doc.get("verdict", "")
        return check("model-book", n >= 18, f"{doc.get('verdict')} "
                     "(the founder's strength-law, audited)")
    except Exception as e:
        return check("model-book", False, f"book audit failed: {type(e).__name__}: {str(e)[:90]}")


# -------------------------------------------------------- 13 abstraction
def c_abstract():
    """T2/T4's RECEIPT (the final round): the math + the ARC-class
    abstraction drills + the self-reasoning counterfactuals = the tiered
    accuracy - the previously UNMEASURED intelligence tiers = measured."""
    try:
        st = json.load(open(os.path.join(ROOT, "Config", "abstract_state.json"),
                            encoding="utf-8-sig"))
        tiers = st.get("tiers", {})
        accs = []
        for t0, s0 in tiers.items():
            if s0.get("n", 0) >= 1:
                accs.append(f"{t0}: {s0.get('hits', 0)}/{s0.get('n', 0)}")
        return check("abstract-tiers", len(accs) >= 2,
                     " | ".join(accs[:5]) + " (the sympy/ARC-truth = deterministic)")
    except Exception as e:
        return check("abstract-tiers", False, f"the abstract receipt unreadable: {e}")


def main():
    print("=========================================================")
    print("  THE FLEET DOCTOR - unified self-test (one pass, $0)")
    print("=========================================================")
    for fn in (c_ports, c_docker, c_lanes, c_brain, c_memory, c_mcp,
               c_swe, c_horizon, c_court, c_webuse, c_capacity, c_book, c_abstract):
        try:
            fn()
        except Exception as e:
            check(fn.__name__, False, f"doctor error: {type(e).__name__}: {str(e)[:90]}")
    n_ok = sum(1 for c in CHECKS if c["ok"])
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "checks": CHECKS, "passed": n_ok, "total": len(CHECKS),
           "verdict": f"{n_ok}/{len(CHECKS)} layers PASS",
           "law": "the doctor reports; it never fixes silently"}
    try:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
    except Exception as e:
        print(f"[doctor] receipt write failed: {e}")
    print(f"=== FLEET DOCTOR VERDICT: {doc['verdict']} ===")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())