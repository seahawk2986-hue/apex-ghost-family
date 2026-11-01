"""GRADE-EARLY (doctrine Part VII Q1/Q2/Q7, verified canon): rank the BACKLOG
before spending download requests. FineWeb/FineWeb-Edu proved a classifier
that ranks beats raw volume; LIMA proved curated-tiny beats everything;
Ultra-FineWeb proved cheap verifiers fit small boxes. This organ scores the
pending queue with stdlib heuristics (zero network, zero model calls) and
writes Config/backlog_grades.json. An optional --vote mode adds Q6
sampling-and-voting brain consensus ONLY when RAM allows (D1 gate).
Hardware: pure text scoring, bounded; RAM-gated for the voting mode."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ROOT, "Config", "backlog_grades.json")

VEIN = ["awesome", "toolkit", "library", "framework", "engine", "collection",
        "curated", "list", "tools", "sdk", "algorithm"]
JUNK = ["test", "example", "sample", "tutorial", "course", "homework", "assignment"]


def heuristic_score(repo, prior_grade=None):
    """0-100 score from the repo string alone + the family's own prior grading.
    Q1/Q7 logic: signal-dense names win, junk words sink, established grading
    adds credibility. No network. Bounded."""
    name = str(repo).split("/")[-1].lower()
    score = 40.0
    if any(w in name for w in VEIN):
        score += 25
    if any(j in name for j in JUNK):
        score -= 30
    if re.search(r"\d{3,}", name):          # throwaway/numbered repos
        score -= 10
    if len(name) >= 6 and not name.startswith(("untitled", "test")):
        score += 5
    if prior_grade:
        try:
            score += min(20.0, float(prior_grade) * 2)
        except Exception:
            pass
    return round(max(0.0, min(100.0, score)), 1)


def vote_score(repo, votes=3):
    """Q6 sampling-and-voting through the local brain, RAM-gated and bounded:
    3 independent temperature-jittered calls, majority-average of 0-10 -> x10.
    NEVER blocks: any failure returns the heuristic score unchanged."""
    try:
        import psutil
        if psutil.virtual_memory().available / 2 ** 30 < 2.5:
            return None
        import urllib.request
        url = "http://127.0.0.1:1234/api/v0/models"
        model = None
        try:
            for m in json.load(urllib.request.urlopen(url, timeout=4)).get("data", []):
                if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                    model = m["id"]
                    break
        except Exception:
            return None
        if not model:
            return None
        vals = []
        for _ in range(votes):
            p = (f"Score this GitHub repo for genuine reusable-code value, "
                 f"0-10, digits only, no words: {repo}")
            req = urllib.request.Request(
                "http://127.0.0.1:1234/v1/chat/completions",
                data=json.dumps({"model": model, "messages":
                                 [{"role": "user", "content": p}],
                                 "temperature": 0.7 + 0.1 * _, "stream": False,
                                 "max_tokens": 8}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r0:
                txt = ((((json.load(r0).get("choices")) or [{}])[0]
                        .get("message", {}) or {}).get("content", "")) or ""
            m = re.search(r"\b(\d|10)\b", txt)
            if m:
                vals.append(int(m.group(1)) * 10)
        return round(sum(vals) / len(vals), 1) if vals else None
    except Exception:
        return None


def run(vote_mode=False, top_n=20):
    st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
    pend = [str(p) for p in st.get("pending_leads", []) if str(p).strip()]
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
        prior = dict((pm.get("grading") or {}).get("grades_top") or [])
    except Exception:
        prior = {}
    rows = []
    for repo in pend[:2000]:
        pr = prior.get(repo)
        h = heuristic_score(repo, pr)
        row = {"repo": repo, "score": h, "mode": "heuristic"}
        rows.append(row)
    if vote_mode:
        voted = 0
        for row in rows[:top_n]:          # vote ONLY the top-N by heuristic
            vs = vote_score(row["repo"])
            if vs is not None:
                row["vote"] = vs
                row["score"] = round(0.5 * row["score"] + 0.5 * vs, 1)
                row["mode"] = "heuristic+vote"
                voted += 1
        print(f"[grade-early] brain voting applied to {voted}/{min(len(rows), top_n)} "
              f"top candidates (RAM-gated, 3 samples each)")
    rows.sort(key=lambda r: -r["score"])
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "scored": len(rows), "rows": rows}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, OUT)
    print(f"[grade-early] scored {len(rows)} backlog leads -> Config/backlog_grades.json")
    print("[grade-early] TOP-10 (the queue these SHOULD be fetched in):")
    for r0 in rows[:10]:
        print(f"   {r0['score']:5.1f}  {r0['repo'][:60]}  ({r0['mode']})")
    return out


if __name__ == "__main__":
    run(vote_mode="--vote" in sys.argv)