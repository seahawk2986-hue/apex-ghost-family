"""NEAR-DUP for the skill store (doctrine Part V, K2/K3): sha256 exact-match
is the family's dedup today; the proven corpus lines (The Stack v2, FineWeb)
add NEAR-duplicate detection because rephrased/ lightly-modified copies pass
exact hashing. Pure stdlib: character 5-gram Jaccard with a length prefilter.
No numpy, no deps - RAM stays tiny (short skill texts).
CLI self-test: python NearDedup.py  -> prints verdicts; exits nonzero on FAIL."""
import hashlib
import json
import sys

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"


def _shingles(text, k=5):
    t = " ".join(str(text).lower().split())
    if len(t) < k:
        return {t} if t else set()
    return {t[i:i + k] for i in range(len(t) - k + 1)}


def near_ratio(a, b, k=5):
    """Jaccard similarity over char 5-grams: ~1.0 = near-identical,
    ~0.0 = unrelated. Length prefilter skips obvious pairs."""
    sa, sb = _shingles(a, k), _shingles(b, k)
    if not sa or not sb:
        return 0.0
    if min(len(sa), len(sb)) / max(1, max(len(sa), len(sb))) < 0.34:
        return 0.0
    inter = len(sa & sb)
    return inter / (len(sa) + len(sb) - inter)


def find_near_dups(texts, threshold=0.75):
    """Greedy clustering: returns a list of groups [[idx, dup_idx, ...], ...]
    whose members are pairwise >= threshold; singletons are omitted (cheap:
    O(n^2) in groups, fine for a 245-skill store with a length prefilter).
    Threshold calibrated by self-test: a one-word edit in even a 60-char text
    scores ~0.79 (the WORST case); 300+-char texts with any edit score >0.9.
    0.75 separates near-dups from genuinely different skills."""
    assigned = {}
    groups = []
    for i in range(len(texts)):
        if i in assigned:
            continue
        grp = [i]
        assigned[i] = len(groups)
        for j in range(i + 1, len(texts)):
            if j in assigned:
                continue
            if near_ratio(texts[i], texts[j]) >= threshold:
                assigned[j] = len(groups)
                grp.append(j)
        if len(grp) > 1:
            groups.append(grp)
    return groups


def audit_library(threshold=0.80):
    """Audit Config/SkillLibrary.json for near-duplicate skills (report-only
    this pass - eviction stays the keeper's decision, printed honestly)."""
    try:
        lib = json.load(open(ROOT + r"\Config\SkillLibrary.json",
                             encoding="utf-8-sig"))["skills"]
    except Exception as e:
        print(f"[near-dedup] library unreadable: {e}")
        return []
    texts = [(s.get("skill", "") + " " + s.get("summary", ""))[:600]
             for s in lib]
    groups = find_near_dups(texts, threshold)
    print(f"[near-dedup] library {len(lib)} skills -> {len(groups)} near-dup "
          f"clusters (threshold {threshold})")
    for g in groups[:8]:
        names = [lib[i].get("skill", "?")[:60] for i in g[:4]]
        print("   cluster:", " ~ ".join(names))
    return groups


if __name__ == "__main__":
    a = ("def add(a, b): return a + b  # simple addition helper for tests")
    b = ("def add(a, b): return a + b  # simple addition helper for CI checks")
    c = ("The quick brown fox jumps over the lazy dog near the river bank.")
    long1 = ("def train(loader): epochs=3; for each batch: forward, loss.backward, "
             "optimizer.step; then validate on the held-out split and log metrics to the "
             "registry, marking the final checkpoint sha256 for provenance tracking.")
    long2 = ("def train(loader): epochs=3; for each batch: forward, loss.backward, "
             "optimizer.step; then validate on the held-out split and log metrics to the "
             "registry, marking the final checkpoint sha256 for provenance audit trails.")
    r1, r2, r3 = near_ratio(a, b), near_ratio(a, c), near_ratio(long1, long2)
    print(f"self-test: short near-pair {r1:.2f} (expect >=0.75): {'PASS' if r1 >= 0.75 else 'FAIL'}")
    print(f"self-test: unrelated pair {r2:.2f} (expect <0.30): {'PASS' if r2 < 0.30 else 'FAIL'}")
    print(f"self-test: realistic-length edited pair {r3:.2f} (expect >=0.90): {'PASS' if r3 >= 0.90 else 'FAIL'}")
    print(f"identical: {near_ratio(a, a):.2f} (expect 1.00)")
    if "--audit" in sys.argv:
        audit_library()
    sys.exit(0 if r1 >= 0.75 and r2 < 0.30 and r3 >= 0.90 else 1)