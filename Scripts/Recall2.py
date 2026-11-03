"""Recall-2.0 - SEMANTIC MEMORY (the memory 6->10 organ).
Every event in memory_episodic.jsonl gets a local embedding vector (nomic
via LM Studio, $0, in-box). Recall = cosine top-K over a float16 index
(bounded: the LATEST 5000 events = ~7.7MB). Commands:
  build            -> (re)index the latest-5000 events
  query "text"     -> semantic top-5 (cosine)
  append           -> index only NEW rows (the incremental delta)
Fail-closed: the LM-Studio-down = the honest skip; the RAM-gate on build."""
import hashlib
import json
import os
import sys
import time

import numpy as np
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(ROOT, "memory_episodic.jsonl")
VEC = os.path.join(ROOT, "Config", "memory_vectors.npy")
META = os.path.join(ROOT, "Config", "memory_vectors_meta.jsonl")
LM = "http://127.0.0.1:1234/v1/embeddings"
MODEL = "text-embedding-nomic-embed-text-v1.5"
CAP = 5000          # the bounded window (the honest memory = the newest)
BATCH = 32


def embed(texts):
    for attempt in range(3):
        try:
            r = rq.post(LM, json={"model": MODEL, "input": texts}, timeout=120)
            r.raise_for_status()
            vecs = [d["embedding"] for d in r.json()["data"]]
            return np.array(vecs, dtype=np.float32)
        except rq.HTTPError as e:
            if attempt == 2:
                raise
            time.sleep(12 * (attempt + 1))   # the load-race cure
    raise RuntimeError("unreachable")


def rows():
    out = []
    try:
        for ln in open(LEDGER, encoding="utf-8-sig", errors="ignore"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out[-CAP:]


def row_text(r):
    return (str(r.get("kind", "event")) + ": " + str(r.get("text", ""))
            [:600] + " | " + str(r.get("meta", {}))[:200])


def fpr(x):
    return int(hashlib.sha1(x.encode("utf-8", "replace")).hexdigest()[:12], 16)


def build():
    import psutil
    free = psutil.virtual_memory().available / 2 ** 30
    if free < 0.8:
        print(f"[RAM-gate]: {free:.2f}GB free < 0.8 - the build = honest-skip")
        return
    rs = rows()
    print(f"[build]: {len(rs)} events (the latest-{CAP} window)", flush=True)
    vecs, metas = [], []
    t0 = time.time()
    for i in range(0, len(rs), BATCH):
        chunk = rs[i:i + BATCH]
        try:
            v = embed([row_text(r) for r in chunk])
        except Exception as e:
            print(f"[embed-fail @ {i}]: {str(e)[:70]} - the honest stop")
            break
        vecs.append(v.astype(np.float16))
        for r, j in zip(chunk, range(i, i + v.shape[0])):
            metas.append({"fpr": fpr(row_text(r)), "ts": r.get("ts", ""),
                          "kind": r.get("kind", ""), "row": j})
        if (i // BATCH) % 10 == 0:
            print(f"  {i + len(chunk)}/{len(rs)} ({round(time.time() - t0, 1)}s)",
                  flush=True)
    if not vecs:
        print("[build]: nothing embedded (the honest empty)")
        return
    V = np.concatenate(vecs).astype(np.float16)
    V = V / (np.linalg.norm(V.astype(np.float32), axis=1, keepdims=True)
             .astype(np.float16).clip(1e-6))
    np.save(VEC, V)
    with open(META, "w", encoding="utf-8") as f:
        for m in metas:
            f.write(json.dumps(m) + "\n")
    print(f"[built]: {V.shape} index -> Config (float16, "
          f"{round(os.path.getsize(VEC) / 2 ** 20, 1)}MB)")


def append_delta():
    rs = rows()
    meta = [json.loads(l) for l in open(META, encoding="utf-8-sig")] \
        if os.path.exists(META) else []
    known = {m["fpr"] for m in meta}
    new = [r for r in rs if fpr(row_text(r)) not in known]
    if not new:
        print("[delta]: nothing new")
        return
    v = embed([row_text(r) for r in new]).astype(np.float16)
    v = v / np.linalg.norm(v.astype(np.float32), axis=1, keepdims=True).astype(np.float16).clip(1e-6)
    V = np.load(VEC) if os.path.exists(VEC) else np.zeros((0, 0), np.float16)
    V2 = np.concatenate([V, v]) if V.size else v
    # THE 2026-11-04 FIX (the audited CAP drift): the index grew beyond CAP
    # forever; now both vectors and metas are truncated to the newest CAP
    # (and META is REWRITTEN, not appended - the alignment is enforced).
    metas = list(meta)
    base = len(V) if V.size else 0
    for r0 in new:
        metas.append({"fpr": fpr(row_text(r0)), "ts": r0.get("ts", ""),
                      "kind": r0.get("kind", ""), "row": base})
        base += 1
    overflow = V2.shape[0] - CAP
    if overflow > 0:
        V2 = V2[overflow:]
        metas = metas[overflow:]
        for i, m0 in enumerate(metas):
            m0["row"] = i
        print(f"[delta]: CAP enforced - trimmed {overflow} oldest rows")
    np.save(VEC, V2)
    with open(META, "w", encoding="utf-8") as f:
        for m0 in metas:
            f.write(json.dumps(m0) + "\n")
    print(f"[delta]: +{len(new)} vectors -> {V2.shape[0]} total (CAP {CAP})")


def _reindex_rows():
    """After CAP-trims the meta 'row' fields stay only as a fallback; rows are
    matched by fingerprint at query time (see query())."""


def query(text, k=5):
    if not (os.path.exists(VEC) and os.path.exists(META)):
        print("[query]: no index - run build first")
        return
    q = embed([text])[0].astype(np.float32)
    q = q / (np.linalg.norm(q) + 1e-6)
    V = np.load(VEC).astype(np.float32)
    meta = [json.loads(l) for l in open(META, encoding="utf-8-sig")]
    rs = rows()
    # THE 2026-11-04 FIX (the audited drift): meta "row" indices were built
    # against an older window - archiving slid the file; the clamp silently
    # returned the WRONG event. Now: fingerprint-match into the CURRENT
    # window first (fpr is the stable key), row-index just a fallback.
    try:
        cur = {}
        for i, r0 in enumerate(rs):
            cur.setdefault(fpr(row_text(r0)), i)
    except Exception:
        cur = {}
    sims = V @ q
    top = np.argsort(-sims)[:k]
    print(f"[recall-2.0 for '{text[:60]}']:")
    for t in top:
        m = meta[t] if t < len(meta) else {}
        ri = cur.get(m.get("fpr"), min(m.get("row", len(rs) - 1), len(rs) - 1)) \
            if rs else 0
        r = rs[ri] if rs else {}
        drift = " (fpr-anchored)" if m.get("fpr") in cur else " (row-fallback)"
        print(f"  {sims[t]:.3f}  [{m.get('kind', '?')}] "
              f"{str(r.get('text', ''))[:110]}{drift}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "append":
        append_delta()
    elif cmd == "query":
        query(" ".join(sys.argv[2:]) or "recent lessons")
    else:
        print("usage: Recall2.py build|append|query \"text\"")