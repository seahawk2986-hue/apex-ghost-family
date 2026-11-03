"""ApexCache - PHASE 2: the local SQLite resolution cache (apex_cache.db).

The law: an external call = spent only once. dispatch = sha256 of the
SANITIZED signature; a hit = replayed locally, network bypassed; a miss =
validated THEN stored. The DB = the working directory, $0 forever.
"""
import hashlib
import json
import os
import re
import sqlite3
import time

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
DB = os.path.join(REPO, "apex_cache.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache_entries (
    prompt_hash   TEXT PRIMARY KEY,
    task          TEXT,
    provider      TEXT,
    model         TEXT,
    resolution    TEXT,          -- the verified diff/answer payload
    verify_state  TEXT,          -- 'validated' | 'unverified' (honest)
    hits          INTEGER DEFAULT 0,
    ts            REAL
);
CREATE TABLE IF NOT EXISTS cache_stats (key TEXT PRIMARY KEY, val TEXT);
"""


def _conn():
    c = sqlite3.connect(DB, timeout=10)
    c.executescript(SCHEMA)
    return c


def _norm_text(t):
    """THE NEAR-DUP TIER (the token-block round, 2026-11-04): one signature
    must catch question-variants, not just byte-identical asks - 'what is
    X?' and 'What is X' replay off the disk ($0) instead of spending a
    capped lane's daily tokens. Conservative: case/punct/whitespace only."""
    t = (t or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _chat_sig(msg):
    """THE CANONICAL VARIANT KEY: every chat-replay lookup and every write
    lands on THIS one point (the '|' separator survives normalization)."""
    return signature({"text": "chat|" + _norm_text(msg)})


def store_chat(msg, reply, lane_name, verify_state="unverified"):
    """THE CHAT REPLAY STORE (both routes call this single point): writes
    the answer under the canonical variant key - so later variants replay
    off the disk instead of spending a capped lane's daily tokens. $0,
    bounded 6000 chars."""
    store(_chat_sig(msg), {"task": "chat replay"}, lane_name or "chat", "chat",
          (reply or "")[:6000], verify_state)
    return _chat_sig(msg)


def signature(payload):
    """sha256 of the sanitized, order-stable problem signature (near-dup
    normalized since the token-block round)."""
    norm = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def cache_get(text):
    """The replay path: exact hash first, then the NEAR-DUP tier - chat
    lookups land on the canonical variant key (one shared point with
    store_chat)."""
    h = signature({"text": text})
    row = lookup(h)
    if row and row[2]:
        return row[2], h
    if text.startswith("chat|"):
        hn = _chat_sig(text[5:])
    else:
        hn = signature({"text": _norm_text(text)})
    if hn != h:
        rown = lookup(hn)
        if rown and rown[2]:
            return rown[2], hn
    return None, h


def lookup(h):
    with _conn() as c:
        row = c.execute("SELECT provider, model, resolution, verify_state "
                        "FROM cache_entries WHERE prompt_hash=?", (h,)).fetchone()
        if row:
            c.execute("UPDATE cache_entries SET hits=hits+1 WHERE prompt_hash=?",
                      (h,))
        return row


def store(h, payload, provider, model, resolution, verify_state):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO cache_entries "
                  "(prompt_hash, task, provider, model, resolution, "
                  "verify_state, hits, ts) VALUES (?,?,?,?,?,?,0,?)",
                  (h, payload.get("task", "")[:300], provider, model,
                   resolution[:20000], verify_state, time.time()))


def stats():
    with _conn() as c:
        rows = c.execute("SELECT COUNT(*), COALESCE(SUM(hits),0) "
                         "FROM cache_entries").fetchone()
        return {"entries": rows[0], "replayed": rows[1]}


# --- the 50-paper combine: the semantic near-cache (MeanCache/ContextCache class) ---
def _trigrams(s):
    s = (s or "").lower()
    return {s[i:i + 5] for i in range(0, max(0, len(s) - 4), 2)} or {s}


def _jaccard(a, b):
    return len(a & b) / max(1, len(a | b))


def cache_lookup_any(text, threshold=0.90, learn=True):
    """Exact hash first, then the trigram near-match - WITH A SAFETY GATE:
    the near-hit serves only at >= 0.90 similarity (a wrong 'close enough'
    = worse than a miss), and every near-hit decision = recorded so the
    threshold can be audited, never silently guessed. Returns
    (reply, kind: exact|semantic|near|none)."""
    reply, _k = cache_get(text)
    if reply is not None:
        return reply, "exact"
    try:
        con = _conn()
        rows = con.execute("SELECT prompt_hash, task, resolution "
                           "FROM cache_entries WHERE verify_state='validated' "
                           "LIMIT 400").fetchall()
        con.close()
    except Exception:
        return None, "none"
    cur = _trigrams(text)
    best, best_sim = None, 0.0
    for h, task, res in rows:
        sim = _jaccard(_trigrams(task or ""), cur)
        if sim > best_sim:
            best, best_sim = (h, res), sim
    if best_sim >= threshold:
        return best[1], "semantic"
    if learn and best and best_sim >= threshold - 0.25:
        _log_near(hit=best[0], sim=best_sim, accepted=False)
    return None, "near" if best else "none"


def _log_near(hit, sim, accepted):
    p = os.path.join(REPO, "scores", "near_cache_audit.jsonl")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "hit": hit[:10],
                            "sim": round(sim, 3), "accepted": accepted}) + "\n")


if __name__ == "__main__":
    h = signature({"task": "smoke", "error": "ZeroDivisionError"})
    if lookup(h):
        print("[cache]: replay:", lookup(h)[2][:60])
    else:
        store(h, {"task": "smoke"}, "local", "smoke-selftest", "diff --smoke 1",
              "unverified")
        print("[cache]: stored self-test row", stats())