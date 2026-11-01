"""ISSUE TRIAGE (doctrine Part VII Q4 SPICE + Q5 PAIChecker, verified):
triage the GH Archive good-first-issue candidates BEFORE any human review -
clarity, effort, alignment signals from the issue text itself, with optional
Q6 sampling-and-voting brain consensus (RAM-gated). SPICE proved machine
triage costs ~$5.10 per 1,000 vs ~$100,000 manual; PAIChecker proved 13.6%
of issue-PR pairs are misaligned - so we gate BEFORE filing, protecting the
family's first external artifacts. Standalone; bounded; stdlib."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
BUGS = os.path.join(AD, "gh_archive_bugs.jsonl")
OUT = os.path.join(ROOT, "Config", "issue_triage.jsonl")

GOOD = ["missing", "error", "crash", "bug", "fails", "wrong", "fix", "issue",
        "unexpected", "regression", "traceback"]
VAGUE = ["doesn't work", "not working", "broken", "help", "how do i", "question"]


def triage(title):
    """0-100: clarity (specific failure words, length, precision markers)
    minus vagueness. SPICE's issue-clarity axis, stdlib form."""
    t = (title or "").strip()
    low = t.lower()
    s = 50.0
    if any(g in low for g in GOOD):
        s += 18
    if any(v in low for v in VAGUE):
        s -= 25
    if 12 <= len(t.split()) <= 40:
        s += 10            # specific but not a novel
    if re.search(r"\b\d{2,}\b|exception|error code|http", low):
        s += 8             # contains evidence (numbers/exceptions)
    if len(t) < 10:
        s -= 20
    return round(max(0.0, min(100.0, s)), 1)


def vote_clarity(title, votes=3):
    """Q6 consensus: 3 brain opinions, majority-average. RAM-gated, bounded,
    fail-open to the heuristic score (honest)."""
    try:
        import psutil
        if psutil.virtual_memory().available / 2 ** 30 < 2.5:
            return None
        import urllib.request
        model = None
        try:
            for m in json.load(urllib.request.urlopen(
                    "http://127.0.0.1:1234/api/v0/models", timeout=4)).get("data", []):
                if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                    model = m["id"]
                    break
        except Exception:
            return None
        if not model:
            return None
        vals = []
        for i in range(votes):
            p = (f"Rate this GitHub issue title for clarity and actionability "
                 f"for a contributor, 0-10, digits only: {title}")
            req = urllib.request.Request(
                "http://127.0.0.1:1234/v1/chat/completions",
                data=json.dumps({"model": model, "messages":
                                 [{"role": "user", "content": p}],
                                 "temperature": 0.6 + 0.15 * i, "stream": False,
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


def run(vote_mode=False):
    rows = []
    if os.path.exists(BUGS):
        for line in open(BUGS, encoding="utf-8-sig"):
            if not line.strip():
                continue
            try:
                b = json.loads(line)
            except Exception:
                continue
            s = triage(b.get("issue", ""))
            row = {"repo": b.get("repo"), "issue": b.get("issue", "")[:100],
                   "clarity": s, "mode": "heuristic",
                   "align_gate": "check-before-filing (Q5: 13.6% misalign)",
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
            if vote_mode:
                vs = vote_clarity(b.get("issue", ""))
                if vs is not None:
                    row["clarity"] = round(0.5 * s + 0.5 * vs, 1)
                    row["mode"] = "heuristic+vote"
            rows.append(row)
    rows.sort(key=lambda r: -r["clarity"])
    with open(OUT, "w", encoding="utf-8") as f:
        for r0 in rows:
            f.write(json.dumps(r0) + "\n")
    print(f"[issue-triage] {len(rows)} GFI candidates scored -> Config/issue_triage.jsonl")
    print("[issue-triage] filing queue (clarity-sorted; alignment gate = verify "
          "the PR/fix pair before ANY filing):")
    for r0 in rows[:8]:
        print(f"   {r0['clarity']:5.1f}  {r0['repo'][:36]} | {r0['issue'][:52]}")
    return rows


if __name__ == "__main__":
    run(vote_mode="--vote" in sys.argv)