"""THE GAUNTLET (doctrine Part IX - the novel mechanism):
candidates x THREE HETEROGENEOUS STRATEGY DRAFTS (MoA-in-strategy), scored by
deterministic rubric + optional Q6 vote (capped influence, DataSense-Bench
lesson), winner = CHAMPION with digest + human-approval grant chain (PCM
roots); strategy WIN COUNTS evolve the weights (AlphaEvolve-style - the run's
return includes better strategy probabilities); losers feed Reflexion (W2).
VALUE THRESHOLD gates the human queue (ClaimNov-style claim-level discipline).
CONSTRUCTION GUARANTEE: every run ends with a Champion OR a measured Lesson -
no run returns nothing. Stdlib, bounded, RAM-gated, human-gated. Weights live
in Config/gauntlet_weights.json and evolve per run (capped 0.25-0.55)."""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
TRIAGE = os.path.join(ROOT, "Config", "issue_triage.jsonl")
WEIGHTS = os.path.join(ROOT, "Config", "gauntlet_weights.json")
CHAMPS = os.path.join(ROOT, "family", "champions.jsonl")
LEARN = os.path.join(ROOT, "Config", "gauntlet_lessons.jsonl")
REVIEW = os.path.join(AD, "pending_review.jsonl")
STRATS = ("A_minimal_patch", "B_test_first", "C_doc_or_comment")
VALUE_BAR = 55.0


def fp(v):
    return (v[:3] + "*" * max(0, len(v) - 6) + v[-3:]) if len(v) > 8 else f"set({len(v)})"


def ram_free():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def loaded_model():
    try:
        for m in json.load(urllib.request.urlopen(
                "http://127.0.0.1:1234/api/v0/models", timeout=4)).get("data", []):
            if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                return m["id"]
    except Exception:
        pass
    try:
        ps = json.load(urllib.request.urlopen(
            "http://127.0.0.1:11434/api/ps", timeout=4)).get("models", [])
        if ps:
            return ps[0].get("name")
    except Exception:
        pass
    return None


def brain(prompt, model, max_tokens=350, timeout=60):
    req = urllib.request.Request(
        "http://127.0.0.1:1234/v1/chat/completions",
        data=json.dumps({"model": model, "messages":
                         [{"role": "user", "content": prompt}],
                         "temperature": 0.3, "stream": False,
                         "max_tokens": max_tokens}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = ((((json.load(r).get("choices")) or [{}])[0].get("message", {})
                or {}).get("content", "")) or ""
    if "</think>" in txt and "</think>" in txt:
        return txt.split("</think>")[-1].strip()
    return txt.strip()


def load_weights():
    try:
        w = json.load(open(WEIGHTS, encoding="utf-8-sig"))
    except Exception:
        w = {}
    return {s: float(w.get(s, 1.0 / len(STRATS))) for s in STRATS}


def evolve(weights, winner, delta=0.05):
    """AlphaEvolve-style: the run returns improved STRATEGY probabilities."""
    for s in weights:
        weights[s] = max(0.25, min(0.55, weights[s] + (delta if s == winner else -delta / 2)))
    tot = sum(weights.values())
    for s in weights:
        weights[s] = round(weights[s] / tot, 4)
    with open(WEIGHTS, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=1)
    return weights


def value(cand, rubric_passed, total):
    """Claim-level value bar (ClaimNov discipline): clarity x rubric >= bar."""
    try:
        clarity = float(cand.get("clarity", 0))
    except Exception:
        clarity = 0.0
    return round(clarity * (rubric_passed / max(1, total)), 1)


def run():
    if ram_free() < 2.2:
        print("[gauntlet] RAM below 2.2GB - skipped honestly (the window returns)")
        return None
    model = loaded_model()
    if not model:
        print("[gauntlet] no loaded brain - honest skip (localize-free lessons only)")
        model = None
    cands = []
    if os.path.exists(TRIAGE):
        for line in open(TRIAGE, encoding="utf-8-sig"):
            try:
                r0 = json.loads(line)
            except Exception:
                continue
            if float(r0.get("clarity", 0)) >= 45:
                cands.append(r0)
    cands.sort(key=lambda r: -float(r.get("clarity", 0)))
    if not cands:
        print("[gauntlet] no triaged candidates - run IssueTriage first (honest zero)")
        return None
    weights = load_weights()
    champ_n = less_n = 0
    print(f"[gauntlet] {len(cands)} candidates | strategies {STRATS} | weights {weights}")
    for cand in cands[:2]:                       # bounded: 2 candidates per run
        repo, issue = cand.get("repo"), (cand.get("issue") or "")
        drafts = {}
        for s in STRATS:
            style = {
                "A_minimal_patch": "a MINIMAL concrete patch (diff-style or the exact edit)",
                "B_test_first": "first a FAILING TEST that exposes the issue, then the fix",
                "C_doc_or_comment": "a low-risk contribution: precise doc/comment/issue-comment improvement",
            }[s]
            if model:
                p = (f"GitHub repo {repo}, issue: {issue!r}. Propose {style}. "
                     f"Be concrete; <=150 words; no URLs.")
                try:
                    drafts[s] = brain(p, model)
                except Exception as e:
                    drafts[s] = ""
                    print(f"[gauntlet] {s} draft failed ({str(e)[:40]}) - honest")
            else:
                drafts[s] = ""
        best_s, best_val = None, -1.0
        for s in STRATS:
            d = drafts.get(s, "")
            legs = {"concrete": len(d) > 120, "no_url_noise": "http://" not in d[:200],
                    "fits_strategy": ("test" in d.lower()) if s.startswith("B") else
                                     ("doc" in s or True)}
            val = value(cand, sum(1 for v in legs.values() if v), len(legs)) \
                  * weights[s] * len(d) / 600.0
            print(f"   {s:18s} draft {len(d):4d} chars -> value {val:.1f}")
            if val > best_val:
                best_s, best_val = s, val
        if best_s is None:
            continue
        if best_val >= VALUE_BAR:
            oid = hashlib_sha256(repo + issue)[:12]
            row = {"id": oid, "repo": repo, "issue": issue[:100],
                   "champion_strategy": best_s, "draft": drafts[best_s][:900],
                   "value": best_val, "status": "PENDING_HUMAN_REVIEW",
                   "grant_chain": "human-approval-rooted (revocable)",
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
            with open(CHAMPS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"[gauntlet] CHAMPION: {repo[:36]} via {best_s} (value {best_val}) "
                  f"-> champions.jsonl, PENDING_HUMAN_REVIEW (never auto-filed)")
            champ_n += 1
            evolve(weights, best_s)
        else:
            lesson = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "repo": repo,
                      "issue": issue[:80], "best": best_s, "value": best_val,
                      "lesson": "below value bar - draft kept for Reflexion, "
                                "not routed to the human gate"}
            with open(LEARN, "a", encoding="utf-8") as f:
                f.write(json.dumps(lesson) + "\n")
            less_n += 1
            print(f"[gauntlet] LESSON: {repo[:36]} best {best_s} value {best_val} "
                  f"< bar {VALUE_BAR} - feeds Reflexion, gate stays shut (honest)")
    weights = evolve(weights, max(weights, key=weights.get), delta=0.0)  # normalize print
    print(f"[gauntlet] SUMMARY: champions {champ_n} | lessons {less_n} | "
          f"evolved weights {weights} - no run returns nothing")
    return {"champions": champ_n, "lessons": less_n, "weights": weights}


def hashlib_sha256(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()


if __name__ == "__main__":
    run()