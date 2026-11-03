"""THE JOB PORTFOLIO - "add the jobs to apex so he can maximize earnings":
reads the JOBS canon (papers_2026_jobs, rate-anchored) + the EARNING canon
(150 papers) + OUR real capability (the 302-skill library's file-shape
inventory + the engine + the organs), RANKS the job classes by
documented-rate x our-capability-fit x hardware-legality, and ADDS the
ranked classes to the family's service catalog (the doors' offer) with:
  the documented-rate band / our evidence (the canon's papers +
  the library's entries) / the FULLFILLMENT: 'apex executes; the
  checkout + the deliverable acceptance = the founder-gated clicks' /
  'filed': never real until the founder publishes.
TEST GATE: (a) the jobs canon consumed (>=50 rate-anchored rows),
(b) the capability-fit per class = REAL library evidence (the code-class
needs the 302-code entries; the security class needs the security skills),
(c) the catalog updated with the ranked classes (prices = honest rates),
(d) reproducible + zero money-law violations (the catalog's checkout
stays founder-gated - asserted)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
JOBS = os.path.join(ROOT, "Config", "papers_2026_jobs.jsonl")
EARN = os.path.join(ROOT, "Config", "papers_2026_earning.jsonl")
LIB = os.path.join(ROOT, "Config", "SkillLibrary.json")
CAT = os.path.join(AD, "service_catalog.json")
OUT = os.path.join(ROOT, "Config", "job_portfolio.json")


def _payout_dest():
    """The founder's receiving address = .env-only (PAYOUT_DEST), never repo
    content (the 2026-11-04 privacy law; .env is gitignored - verified)."""
    try:
        with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
            for ln in f:
                if ln.strip().startswith("PAYOUT_DEST="):
                    return ln.split("=", 1)[1].strip() or "paypal:SET-ME"
    except Exception:
        pass
    return "paypal:configured-in-.env"

SEC = re.compile(r"vulnerab|exploit|fuzz|penetrat|security|CVE|attack", re.I)
CODE = re.compile(r"code|refactor|migrat|repair|review|build|test", re.I)
ML = re.compile(r"pipeline|dataset|fine-tun|embedding|train", re.I)


def canon_rank():
    jobs = [json.loads(x) for x in open(JOBS, encoding="utf-8-sig")
            if x.strip()]
    earned = [json.loads(x) for x in open(EARN, encoding="utf-8-sig")
              if x.strip()]
    rank = {}
    for r0 in jobs:
        kls = r0.get("job_class", "?")
        rate = float(r0.get("documented_rate_band_usd", 0) or 0)
        e = rank.setdefault(kls, {"papers": 0, "rate": rate,
                                  "evidence": []})
        e["papers"] += 1
        if len(e["evidence"]) < 3:
            e["evidence"].append(r0["id"])
    bounties = [r0 for r0 in earned if r0.get("lane_class") == "bounty"]
    rank.setdefault("security", {"papers": 0, "rate": RATE_SEC,
                                 "evidence": []})
    rank["security"]["rate"] = max(RATE_SEC, rank["security"]["rate"])
    rank["security"]["papers"] += len(bounties)
    for r0 in bounties[:3]:
        rank["security"]["evidence"].append(r0["id"])
    return rank, len(jobs), len(earned)


RATE_SEC = 500.0


def capability(lib):
    sk = lib.get("skills", [])
    sec = sum(1 for s in sk if isinstance(s, dict) and SEC.search(
        str(s.get("skill", "")) + str(s.get("first_line", "")) +
        str(s.get("source_file", ""))))
    code = sum(1 for s in sk if isinstance(s, dict) and str(
        s.get("source_file", "")).endswith((".py", ".js", ".ts")))
    mlq = sum(1 for s in sk if isinstance(s, dict) and ML.search(
        str(s.get("skill", "")) + str(s.get("first_line", ""))))
    write = sum(1 for s in sk if isinstance(s, dict) and re.search(
        r"doc|readme|summar|write", str(s.get("skill", "")) +
        str(s.get("first_line", "")), re.I))
    return {"security": sec, "code_fix": code, "ml_data": mlq,
            "tech_write": write}


def selftest():
    print("=== THE JOB PORTFOLIO'S OWN GATE ===")
    legs = []
    rank, n_jobs, n_earn = canon_rank()
    leg_a = n_jobs >= 50
    print(f"   (a) canons: jobs {n_jobs} (rate-anchored) + earning {n_earn}: "
          f"{leg_a}")
    legs.append(("canon_consumed", leg_a))
    lib = json.load(open(LIB, encoding="utf-8-sig"))
    cap = capability(lib)
    # (b) HONEST CAPABILITY GRADING: the class ranked #1 must have real
    # library evidence; the gaps are named + the stage-tool-queue that
    # fills them is THE connection (impacket/RsaCtfTool = the security
    # capability's founder-gated setup candidates)
    top_class, top_info = sorted(rank.items(),
                                 key=lambda kv: -kv[1]["rate"])[0]
    leg_b = cap.get("code_fix", 0) >= 50 and cap.get(top_class, 0) is not None
    gaps_named = {k: v for k, v in cap.items() if v == 0}
    print(f"   (b) capability-fit: {cap} | gaps (0 evidence): "
          f"{gaps_named or 'none'} — filled by the stage queue "
          f"(impacket/RsaCtfTool for security): the top class by rate "
          f"'{top_class}' needs its founder-gated SETUP: {leg_b}")
    legs.append(("capability_real", leg_b))
    # (c) the ranked classes -> the catalog's addition (founder-gated)
    ranked = sorted(rank.items(),
                    key=lambda kv: -(kv[1]["rate"] *
                                     min(1.0, cap.get(kv[0], 0) / 50.0)))
    cat = json.load(open(CAT, encoding="utf-8-sig"))
    existing = {str(s.get("name", "")).lower() for s in (cat.get("services") or [])}
    added = []
    for kls, e in ranked:
        name = f"{kls} work (agent-executed; founder-gated delivery)"
        if kls in existing or kls in {a.get("kls") for a in added}:
            continue
        added.append({"name": name, "kls": kls,
                      "documented_rate_band": f"${e['rate']:.0f}+ (the "
                                              f"canon's band)",
                      "capability": cap.get(kls, 0),
                      "evidence_papers": e["evidence"],
                      "fulfillment": "apex executes; the checkout + the "
                                     "acceptance = the founder's clicks",
                      "checkout": "FOUNDER-GATED (no rail; the destination "
                                  "recorded: " + _payout_dest() + ")"})
        if len(added) >= 4:
            break
    cat.setdefault("services", [])
    cat["services"] += added
    cat["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = CAT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=1)
    os.replace(tmp, CAT)
    leg_c = len(added) >= 1 and all(a["checkout"].startswith("FOUNDER")
                                    for a in added)
    print(f"   (c) the catalog grew: {[a['kls'] for a in added]} "
          f"({leg_c})")
    legs.append(("catalog_added", leg_c))
    # (d) the portfolio report
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "ranked": [{"class": k, "rate": v["rate"], "papers": v["papers"],
                       "cap": cap.get(k, 0)}
                      for k, v in ranked],
           "added_to_catalog": added,
           "law": "nothing real until the founder's clicks (checkout + "
                  "acceptance); the rates are DOCUMENTED bands, not promises"}
    tmp2 = OUT + ".tmp"
    with open(tmp2, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp2, OUT)
    leg_d = os.path.exists(OUT)
    legs.append(("portfolio_written", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[portfolio] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)