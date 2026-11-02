"""ApexCache - PHASE 2: the local SQLite resolution cache (apex_cache.db).

The law: an external call = spent only once. dispatch = sha256 of the
SANITIZED signature; a hit = replayed locally, network bypassed; a miss =
validated THEN stored. The DB = the working directory, $0 forever.
"""
import hashlib
import json
import os
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


def signature(payload):
    """sha256 of the sanitized, order-stable problem signature."""
    norm = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


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


if __name__ == "__main__":
    h = signature({"task": "smoke", "error": "ZeroDivisionError"})
    if lookup(h):
        print("[cache]: replay:", lookup(h)[2][:60])
    else:
        store(h, {"task": "smoke"}, "local", "smoke-selftest", "diff --smoke 1",
              "unverified")
        print("[cache]: stored self-test row", stats())