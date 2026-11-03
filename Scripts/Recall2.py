"""Recall2 - SEMANTIC MEMORY (the memory 6->10 organ).
Every event in memory_episodic.jsonl gets a local embedding vector (nomic
via LM Studio, $0, in-box). Recall = cosine top-K over a float16 index
(bounded: the LATEST 5000 events = ~7.7MB). Commands:
  build            -> (re)index the latest-5000 events
  query "text"     -> semantic top-5 (cosine)
  append           -> index only NEW rows (the incremental delta)
Fail-closed: the LM-Studio-down = the honest skip; the RAM-gate on build.

2026-11-04 MEMORY ROUND (re-issued + re-sealed - the file was silently
reverted once between edit and commit; the round's write-guard law now
re-seals via ApexGuard after every deliberate change):
  - query2(): the SILENT IMPORTABLE query (the chat's deep_recall consumes
    it; never prints, never raises) - THE SHELF-WARE REVIVAL: nothing had
    EVER executed this index in the machine's life until the chat did;
  - the fpr-anchored retrieval: rows match by CONTENT FINGERPRINT into the
    CURRENT window (the archived-window drift can no longer show the WRONG
    event; row-index stays only as the fallback);
  - the CAP law enforced in append_delta (both vectors AND metas truncated
    aligned; META rewritten, not appended);
  - the delegating CLI lens kept.
"""
import hashlib
import io
import json
import os
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

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
    return str(r.get("text", "")) or json.dumps(r.get("meta", {}), ensure_ascii=False)


def fpr(text):
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def build():
    vecs, metas = [], []
    rs = rows()
    t0 = time.time()
    if _free_gb() < 2.0:
        print("[build]: RAM below the gate - the honest skip")
        return
    for i in range(0, len(rs), BATCH):
        chunk = rs[i:i + BATCH]
        v = embed([row_text(r) for r in chunk]).astype(np.float16)
        vecs.append(v)
        for r, j in zip(chunk, range(i, i + len(chunk))):
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


def _free_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


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
    # THE CAP LAW (2026-11-04): the index grows forever no longer; both
    # vectors and metas truncate ALIGNED to the newest CAP (META REWRITTEN).
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


def query2(text, k=5, kinds=None):
    """THE SILENT IMPORTABLE QUERY (the shelf-ware revival; 2026-11-04):
    same retrieval as the CLI, but returns structured rows and NEVER
    prints/raises; the chat's deep_recall consumes it. Honest empty list."""
    try:
        out = []
        if not (os.path.exists(VEC) and os.path.exists(META)):
            return []
        q = embed([text])[0].astype(np.float32)
        q = q / (np.linalg.norm(q) + 1e-6)
        V = np.load(VEC).astype(np.float32)
        meta = [json.loads(l) for l in open(META, encoding="utf-8-sig")]
        rs = rows()
        cur = {}
        try:
            for i, r0 in enumerate(rs):
                cur.setdefault(fpr(row_text(r0)), i)
        except Exception:
            cur = {}
        sims = V @ q
        top = np.argsort(-sims)[:max(k * 3, k)]
        for t in top:
            m = meta[t] if t < len(meta) else {}
            if kinds and m.get("kind") not in kinds:
                continue
            ri = cur.get(m.get("fpr"), min(m.get("row", len(rs) - 1), len(rs) - 1)) \
                if rs else 0
            r = rs[ri] if rs else {}
            out.append({"sim": float(sims[t]), "kind": m.get("kind", "?"),
                        "ts": m.get("ts", ""), "text": str(r.get("text", ""))[:200]})
            if len(out) >= k:
                break
        return out
    except Exception:
        return []


def query(text, k=5):
    """The CLI lens (the prints) - delegated to the silent importer."""
    try:
        hits = query2(text, k=k)
        if not hits and not os.path.exists(VEC):
            print("[query]: no index - run build first")
            return
        for r0 in hits:
            print(f"  {r0['sim']:.3f}  [{r0['kind']}] {r0['text'][:110]}")
    except Exception as e:
        print("[query]:", type(e).__name__, str(e)[:60])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "append":
        append_delta()
    elif cmd == "query":
        query(" ".join(sys.argv[2:]) or "the family's purpose", k=5)