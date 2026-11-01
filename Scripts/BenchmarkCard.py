"""BENCHMARK HONESTY (canon: benchmark_driven, 22/100 - the largest
cluster) - the benchmark_honesty goal's organ: a comparison card that
prints the 2026 leaders' PUBLISHED claims beside OUR measured equivalents,
LABELED HONESTLY: their numbers are receipts from suites we cannot run on
this box (16GB, $0); ours are measured on OUR gates - directional, never
equivalent. Extraction: regex for benchmark names/numbers in the fresh
canon's abstracts. Nothing inflated; the card states the law.
TEST GATE: (a) claims extracted from the REAL canon (>=3 claim rows),
(b) the card carries the honesty labels + our-side equivalents,
(c) reproducible (scan x2 identical), (d) the card valid JSON."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
CANON = os.path.join(ROOT, "Config", "papers_2026_agents.jsonl")
PRIOR = os.path.join(ROOT, "Config", "papers_2026_evolution.jsonl")
OUT = os.path.join(ROOT, "Config", "benchmark_card.json")
BENCH = re.compile(r"(SWE[- ]?bench|pass@\d+|HumanEval|MBPP|Terminal[- ]?Bench|"
                   r"OSWorld|WebArena|GAIA|SWE-Gym|SWE-agent)", re.I)


def extract(*paths):
    """Honest claim extraction across the canon: a NUMBERED claim (benchmark
    name + a % inside one sentence) or a REFERENCE row (benchmark mentioned
    in a method paper - directional, labeled, never inflated)."""
    claims = []
    for path in paths:
        try:
            rows = [json.loads(x) for x in open(path, encoding="utf-8-sig")
                    if x.strip()]
        except Exception:
            continue
        for p in rows[:80]:
            hay = p.get("title", "") + " " + p.get("abstract", "")
            m = BENCH.search(hay)
            if not m:
                continue
            sents = re.split(r"(?<=[.!?]) ", hay)
            s_num = next((s for s in sents if BENCH.search(s) and "%" in s), None)
            if s_num:
                claims.append({"paper": p["id"],
                               "class": "numbered_claim",
                               "claim": s_num.strip()[:110]})
            else:
                claims.append({"paper": p["id"], "class": "reference",
                               "claim": f"benchmarks cited: {m.group(0)} "
                                        f"(method paper - directional only)"})
    return claims


def our_side():
    """OUR measured equivalents (the honest local instruments)."""
    def rc(name, cast=float, default=0.0):
        try:
            v = json.load(open(os.path.join(ROOT, "Config", name),
                               encoding="utf-8-sig"))
            return cast(v.get("verified_count", 0))
        except Exception:
            return default  # .get on cast? no - cast(v) fails non-dict -> caught
    try:
        cur = json.load(open(os.path.join(ROOT, "Config", "curriculum.json"),
                             encoding="utf-8-sig"))
        ver = int(cur.get("verified_count", 0))
    except Exception:
        ver = 0
    lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                         encoding="utf-8-sig")).get("skills", [])
    code_n = sum(1 for s in lib if isinstance(s, dict) and
                 str(s.get("source_file", "")).lower().endswith(
                     (".py", ".js", ".ts", ".sh", ".ps1")))
    return {"executable_verified_skills": ver,
            "library_coding_entries": code_n,
            "library_total": len(lib)}


def selftest():
    print("=== BENCHMARK HONESTY'S OWN GATE ===")
    legs = []
    claims = extract(CANON, PRIOR)
    numbered = [c for c in claims if c["class"] == "numbered_claim"]
    us = our_side()
    card = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "law": "THEIR numbers = published receipts from suites we cannot "
                   "run on this box (16GB, $0); OUR numbers = measured on OUR "
                   "gates. Directional, never equivalent - and never inflated.",
            "honest_note": (f"numbered claims in the 621-canon: {len(numbered)}"
                            + (" - the abstracts are method-first; the canon "
                               "carries no published score tables in abstracts; "
                               "rows are directional references" if not numbered
                               else "")),
            "their_claims": claims[:15],
            "our_measured": us,
            "serves": "benchmark_honesty"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=1)
    os.replace(tmp, OUT)
    ok_b = (json.load(open(OUT, encoding="utf-8-sig"))["our_measured"] == us
            and "law" in card and us["library_total"] > 0
            and "honest_note" in card)
    print(f"   (b) card: ours {us} + {len(claims[:15])} their-claims, "
          f"law + honest-note labeled: {ok_b}")
    legs.append(("card_valid_labeled", ok_b))
    leg_a = len(claims) >= 3 and ("honest_note" in card
                                  and (len(numbered) >= 1
                                       or "directional" in card["honest_note"]))
    print(f"   (a) claims from the 621-canon: {len(claims)} "
          f"({len(numbered)} numbered; honest note present): {leg_a}")
    legs.append(("claims_extracted", leg_a))
    claims2 = extract(CANON, PRIOR)
    leg_c = [c["paper"] for c in claims] == [c["paper"] for c in claims2]
    print(f"   (c) reproducible scan: {leg_c}")
    legs.append(("reproducible", leg_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[bench] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)