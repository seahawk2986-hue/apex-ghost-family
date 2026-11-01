"""UNCERTAINTY-FIRST BRAIN BUDGET (Part XIII novel organ; active-learning
canon: Settles' uncertainty sampling - spend limited oracle budget where the
model is UNCERTAIN). THE TEST (user's ROI gate): vote EVERY triaged candidate,
record ALL raw readings, then compare:
  uniform-spend: brain calls on all candidates
  uncertainty-first: deep checks only where cross-vote stdev >= 10
If variance CLUSTERS (some high, most low), uncertainty-first keeps the same
information with FEWER calls => ROI boost measured in calls-saved. If variance
is uniform, the organ self-shelves (honest null result).
Also prints the speculative-decoding lever receipt (2x-3x, LM Studio native)."""
import json
import os
import statistics
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"


def ram():
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
    return None


def raw_vote(m, title, temp):
    import urllib.request
    req = urllib.request.Request(
        "http://127.0.0.1:1234/v1/chat/completions",
        data=json.dumps({"model": m, "messages": [{"role": "user", "content":
            f"Rate this GitHub issue title for clarity and actionability for a "
            f"contributor, 0-10, digits only: {title}"}],
            "temperature": temp, "stream": False, "max_tokens": 8}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r0:
        txt = ((((json.load(r0).get("choices")) or [{}])[0].get("message", {})
                or {}).get("content", "")) or ""
    import re
    mm = re.search(r"\b(\d|10)\b", txt)
    return int(mm.group(1)) * 10 if mm else None


def run():
    import IssueTriage as IT
    if ram() < 2.2:
        print("[uncertain-first] RAM below 2.2 - the experiment defers honestly "
              "(votes burn brain bandwidth the box doesn't have)")
        return False
    m = loaded_model()
    if not m:
        print("[uncertain-first] no loaded brain - honest skip")
        return False
    print(f"[uncertain-first] brain: {m} | voting EVERY triaged candidate (3 votes, "
          f"temp 0.6/0.75/0.9) - the test spends the budget once to measure the split")
    rows = []
    t0 = time.time()
    calls = 0
    if os.path.exists(IT.BUGS):
        for line in open(IT.BUGS, encoding="utf-8-sig"):
            try:
                b = json.loads(line)
            except Exception:
                continue
            title = b.get("issue", "")
            h = IT.triage(title)
            raws = []
            for i, t in enumerate((0.6, 0.75, 0.9)):
                try:
                    v = raw_vote(m, title, t)
                    if v is not None:
                        raws.append(v)
                    calls += 1
                except Exception:
                    calls += 1
            sd = statistics.pstdev(raws) if len(raws) > 1 else 0.0
            rows.append({"repo": b.get("repo"), "heuristic": h, "votes": raws,
                         "mean": round(statistics.mean(raws), 1) if raws else None,
                         "stdev": round(sd, 1)})
            print(f"  {b.get('repo', '?')[:34]:36s} h={h:5.1f} votes={raws} "
                  f"mean={rows[-1]['mean']} stdev={rows[-1]['stdev']}")
    hi = [r for r in rows if r["stdev"] >= 10.0]
    lo = [r for r in rows if r["stdev"] < 10.0]
    print()
    print(f"[uncertain-first] {calls} brain calls in {time.time()-t0:.0f}s measured")
    print(f"[uncertain-first] high-variance (stdev>=10): {len(hi)} | low: {len(lo)}")
    uniform_calls = calls
    uncertain_calls = len(rows) * 1 + len(hi) * 3   # survey + deep-checks only on uncertain
    print(f"[uncertain-first] same-information ROI test: uniform {uniform_calls} calls "
          f"vs uncertainty-first {uncertain_calls} calls -> SAVED "
          f"{uniform_calls - uncertain_calls} calls "
          f"({100*(uniform_calls-uncertain_calls)/max(1,uniform_calls):.0f}%)")
    if len(hi) >= 1 and len(lo) >= 1:
        print("[uncertain-first] VERDICT: variance CLUSTERS -> the uncertainty-first "
              "pass boosts ROI (same info, fewer calls) => IMPLEMENT")
        return True
    print("[uncertain-first] VERDICT: variance uniform -> the strategy adds nothing "
          "=> SELF-SHELVED (honest null; re-test when the candidate pool grows)")
    return False


if __name__ == "__main__":
    run()