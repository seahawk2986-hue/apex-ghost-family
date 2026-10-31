"""The Harvest Utilization Layer - everything mined gets USED.

Frontier goalposts being copied:
 1. RAG-style retrieval: mined skills indexed by the (already-loaded) nomic
    embed engine; consult() returns the best skills for any query - semantic,
    not keyword regex (the datatrove/fineweb "index your corpus" pattern)
 2. Self-play training: graded repos become FORECAST DRILLS for the gym
    (mine code -> predict-what-it-does -> check -> evolve) - openclaw's
    'dreaming' pattern at file-weight
 3. Everything lands in PathMemory as 'use' telemetry
"""
import hashlib
import json
import os
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LIB = os.path.join(ROOT, "Config", "SkillLibrary.json")
INDEX = os.path.join(ROOT, "Config", "HarvestIndex.jsonl")
PATHMEM = os.path.join(ROOT, "Config", "PathMemory.json")
UA = {"Content-Type": "application/json"}
EMB_MODEL = "text-embedding-nomic-embed-text-v1.5"


def embed(texts, cap=8):
    out = []
    for i in range(0, min(len(texts), cap), 6):
        chunk = [t[:1500] for t in texts[i:i + 6]]
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:1234/v1/embeddings",
                data=json.dumps({"model": EMB_MODEL, "input": chunk}).encode(),
                headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            out += [d["embedding"] for d in data.get("data", [])]
        except Exception:
            out += [None] * len(chunk)
    return out


def build_index(max_skills=400):
    """Index every NEW skill; the index is append-only JSONL (file-weight)."""
    lib = json.load(open(LIB, encoding="utf-8-sig"))
    have = set()
    if os.path.isfile(INDEX):
        with open(INDEX, encoding="utf-8-sig") as f:
            for line in f:
                try:
                    have.add(json.loads(line).get("hash"))
                except Exception:
                    continue
    fresh = [s for s in lib.get("skills", []) if s.get("sha256", "")[:32] not in have]
    fresh = fresh[:max_skills]
    vecs = embed([s.get("skill", "") + " " + s.get("source_file", "") + " "
                  + " ".join((s.get("imports") or [])[:4]) for s in fresh], cap=max_skills)
    added = 0
    with open(INDEX, "a", encoding="utf-8") as f:
        for s, v in zip(fresh, vecs):
            if v is None:
                continue
            f.write(json.dumps({"hash": s.get("sha256", "")[:32],
                                "skill": s.get("skill", "")[:80],
                                "repo": s.get("source_repo", ""),
                                "vec": v}, ensure_ascii=False) + "\n")
            added += 1
    return added


def consult(topic, k=3):
    """THE USE PATH: skills the swarm mined, retrieved for any query."""
    rows = []
    try:
        with open(INDEX, encoding="utf-8-sig") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        return []
    if not rows:
        return []
    q = embed([topic], cap=1)
    if not q or q[0] is None:
        return []
    scored = []
    for r0 in rows:
        v = r0.get("vec")
        dot = sum(x * y for x, y in zip(q[0], v)) if v else 0
        na = (sum(x * x for x in q[0])) ** 0.5 + 1e-9
        nb = (sum(x * x for x in v)) ** 0.5 + 1e-9
        scored.append((dot / (na * nb), r0))
    scored.sort(key=lambda t: -t[0])
    return [{"skill": r0["skill"], "repo": r0["repo"], "score": round(s, 3)}
            for s, r0 in scored[:k]]


def gym_lesson_feed(grades, ledger, k=5):
    """SELF-PLAY: high-graded mines become reasoning-gym lessons (predict-output
    drills live where the gym already reads lessons: the episodic store)."""
    best = sorted([(grades.get(f, 0), f, lane) for _k, f, lane, _p in ledger
                   if lane is not None], key=lambda t: -t[0])[:k]
    written = 0
    try:
        ep = open(os.path.join(ROOT, "memory_episodic.jsonl"), "a", encoding="utf-8")
        for grade, full, lane in best:
            if grade < 7:
                continue
            row = {"id": hashlib.md5(("lesson" + full).encode()).hexdigest()[:12],
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "kind": "lesson",
                   "text": f"HARVEST LESSON: {full} (grade {grade}/10, lane {lane}) "
                           f"- mined candidate for forecast drills: predict what its "
                           f"core algorithm does before reading it; check against source.",
                   "imp": 0.8}
            ep.write(json.dumps(row, ensure_ascii=True) + "\n")
            written += 1
        ep.close()
    except Exception:
        pass
    return written


if __name__ == "__main__":
    t0 = time.time()
    added = build_index()
    c = consult("binary search algorithm", 3)
    print(f"index: +{added} skills embedded | consult('binary search'): "
          f"{[x['skill'] for x in c]} | {time.time()-t0:.1f}s")
    pm = {}
    try:
        pm = json.load(open(PATHMEM, encoding="utf-8-sig"))
    except Exception:
        pass
    pm["use"] = {"index_rows": added, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(pm, open(PATHMEM, "w", encoding="utf-8"), indent=1)
    print("telemetry: written")