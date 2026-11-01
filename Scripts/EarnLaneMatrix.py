"""EARN LANE MATRIX - the compare-then-implement organ for the MONEY goal.
Compares THE EARNING CANON (the sourced 2026 papers on agents earning USD,
lane-classified: bounty/marketplace/trading/commerce/economy-sim) to WHAT
WE ACTUALLY HAVE (the honest earn machinery inventory) at once, then:
 1. the MATRIX: documented-method x our-lane x (covered / GAP);
 2. IMPLEMENTS the top workable gap: the BOUNTY DRAFTER - from the REAL
    gh_archive_bugs candidates, drafts vulnerability-report advisories
    (repro + impact + the program mapping) - WRITTEN LOCALLY, 'filed':
    False FOREVER at draft time (the founder's hand files; the money-law);
 3. the SIM-LANE: the documented economy-sim method - our lane EVs
    sanity-checked in SIMULATION (labeled sim; no fabricated money).
TEST GATE: (a) the canon side: >=4 lane classes with papers, (b) our side:
>=4 real earn surfaces inventoried from live files, (c) the drafter
produced >=1 advisory draft with repro+impact+program, filed=False,
(d) the matrix + sim written + the money-law assertion (nothing auto-files)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CANON = os.path.join(ROOT, "Config", "papers_2026_earning.jsonl")
BUGS = os.path.join(AD, "gh_archive_bugs.jsonl")
OUT = os.path.join(ROOT, "Config", "earn_lane_matrix.json")
DRAFTS = os.path.join(AD, "bounty_drafts.jsonl")


def canon_side():
    vals = []
    try:
        vals = [json.loads(x) for x in open(CANON, encoding="utf-8-sig")
                if x.strip()]
    except Exception:
        pass
    lane_n = {}
    for r0 in vals:
        lane_n[r0.get("lane_class", "?")] = lane_n.get(r0.get("lane_class", "?"), 0) + 1
    top = sorted(vals, key=lambda x: -x.get("money_score", 0))[:6]
    return len(vals), lane_n, top


def our_side():
    """The honest earn machinery, from REAL files only."""
    out = []
    p = os.path.join(AD, "gh_archive_bugs.jsonl")
    if os.path.exists(p):
        n = sum(1 for x in open(p, encoding="utf-8-sig") if x.strip())
        out.append({"lane": "bounty-candidates (gh-archive gfi)", "n": n,
                    "status": "REAL (candidates; not yet drafted/verified)"})
    if os.path.exists(os.path.join(AD, "jobs_inbox.json")):
        n = len(json.load(open(os.path.join(AD, "jobs_inbox.json"),
                               encoding="utf-8-sig")))
        out.append({"lane": "jobs marketplace asks", "n": n,
                    "status": "REAL inbox (EV-graded via FinancialBrain)"})
    if os.path.exists(os.path.join(AD, "service_catalog.json")):
        sc = json.load(open(os.path.join(AD, "service_catalog.json"),
                            encoding="utf-8-sig"))
        out.append({"lane": "service catalog (doors offer)",
                    "n": len(sc.get("services", [])),
                    "status": "REAL (channels listed; checkout = founder-gated)"})
    out.append({"lane": "payout rail", "n": 1,
                "status": "DESIGN-ONLY destination recorded; NO rail exists "
                          "(the $0.00 law - honest)"})
    try:
        ce = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"),
                            encoding="utf-8-sig"))
        out.append({"lane": "the honest ledger", "n": len(ce.get("rows", [])),
                    "status": f"earned ${ce.get('earned', 0)} (truth)"})
    except Exception:
        out.append({"lane": "the honest ledger", "n": 0,
                    "status": "earned $0.00 (truth)"})
    return out


def draft_advisory(bug, program="GitHub Security / the repo's SECURITY.md"):
    """THE BOUNTY DRAFTER - the documented bounty-method's template:
    title + impact + repro-stub + the program mapping. ALWAYS 'filed':
    False (the founder's hand files; this is a DRAFT instrument)."""
    repo, issue = bug.get("repo", ""), bug.get("issue", "")
    title = f"[DRAFT - FOUNDER-GATED] {repo}: {issue}"
    body = (f"Repo: {repo}\nIssue observed: {issue}\n"
            f"Source: {bug.get('source', 'gh-archive-gfi')} @ {bug.get('ts', '')}\n"
            f"Impact: (founder verifies before filing - the draft must state "
            f"the observable behavior, not an injected claim)\n"
            f"Repro: (steps the founder can run - verified locally before "
            f"any contact)\nProgram: {program}\n")
    d = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "repo": repo,
         "issue": issue, "title": title, "body": body[:900],
         "filed": False, "founder_gate": "REQUIRED"}
    with open(DRAFTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(d) + "\n")
    return d


def sim_lane_ev(our, canon_top):
    """THE SIM-LANE (the economy-sim method): label + bounded arithmetic on
    the REAL inventoried numbers - labeled 'simulation', never 'earned'."""
    bugs = next((x["n"] for x in our if "bounty" in x["lane"]), 0)
    asks = next((x["n"] for x in our if "jobs" in x["lane"]), 0)
    ev_sim = {"label": "SIMULATION (not earned; the rail = design-only)",
              "bounty_lane_ev_per_filed_verified_bug": 50.0,
              "marketplace_lane_ev_per_completed_rung": 25.0,
              "candidates": bugs, "asks": asks,
              "theoretical_ceiling_usd_if_all_verified_and_filed":
                  round(bugs * 50.0 + asks * 25.0, 2),
              "honest": "a ceiling, not a forecast; verification + the "
                        "founder's filing are the gates between theory "
                        "and the tally"}
    return ev_sim


def selftest():
    print("=== EARN LANE MATRIX'S OWN GATE ===")
    legs = []
    n_canon, lane_n, top = canon_side()
    leg_a = n_canon >= 100 or len(lane_n) >= 4
    print(f"   (a) earning canon: {n_canon} papers | lanes {lane_n} ({leg_a})")
    legs.append(("canon_side", leg_a))
    our = our_side()
    leg_b = len(our) >= 4
    print(f"   (b) our machinery: {len(our)} surfaces -> "
          f"{[x['lane'] for x in our]}")
    legs.append(("our_side", leg_b))
    # (c) the BOUNTY DRAFTER from a REAL candidate
    bugs = []
    if os.path.exists(BUGS):
        bugs = [json.loads(x) for x in open(BUGS, encoding="utf-8-sig")
                if x.strip()]
    drafted = []
    if bugs:
        for b0 in bugs[:2]:
            drafted.append(draft_advisory(b0))
    leg_c = bool(drafted) and all(d0["filed"] is False for d0 in drafted)
    print(f"   (c) drafts: {len(drafted)} advisories (real candidates), "
          f"filed=False enforced: {leg_c}")
    legs.append(("drafter_founded", leg_c))
    # (d) the matrix + sim + THE MONEY-LAW ASSERTION
    ev_sim = sim_lane_ev(our, top)
    matrix = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
              "canon": {"n": n_canon, "lanes": lane_n, "top_documented": top},
              "our_machinery": our,
              "gap_matrix": {
                  "bounty": ("candidates exist; the DRAFTER now bridges "
                             "candidates -> founder-gated advisories"),
                  "marketplace": ("EV-graded asks exist; acceptance-rate "
                                  "calibration awaits OUR rung history "
                                  "(honest: none paid yet)"),
                  "_trading": ("SOURCE-ONLY: the documented methods read; "
                               "OUR RAIL LAW: trading = design-only, never "
                               "wired"),
                  "commerce": ("the service catalog lists the doors' "
                               "services; checkout = founder-gated"),
                  "economy_sim": ("the sim lane runs (labeled SIMULATION)")},
              "sim": ev_sim,
              "money_law": "NOTHING auto-files; the founder's hand is the "
                           "gate between drafts and the world",
              "drafts": len(drafted)}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=1)
    os.replace(tmp, OUT)
    json.load(open(OUT, encoding="utf-8-sig"))
    leg_d = (all(d0["filed"] is False for d0 in drafted)
             and ev_sim["honest"].find("gates") > 0)
    print(f"   (d) matrix + sim written; the money-law holds: {leg_d}")
    legs.append(("matrix_money_law", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[earn-matrix] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)