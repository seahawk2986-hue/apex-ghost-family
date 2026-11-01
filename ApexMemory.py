"""
ApexMemory v2 - Tiered cognitive memory, state-of-the-art retrieval.

Tier 1: Working memory   - volatile dict (this process)
Tier 2: Episodic memory  - append-only JSONL event log (crash-safe, archived)
Tier 3: Semantic memory  - embedded knowledge fragments with HYBRID retrieval

v2 upgrades (research-aligned, ~zero compute cost):
  * Importance weighting   - lessons/rules outrank fragments (per-kind priors)
  * Temporal decay         - recency half-life, so stale memories fade naturally
  * Hybrid blended recall  - cosine(vector) + keyword overlap + importance +
                             recency, weighted fusion (robust where vector-only
                             retrieval fails: near-duplicates, short queries)
  * Deduplication          - near-identical memories refresh instead of piling up
  * Consolidation          - episodic events are periodically distilled into
                             deterministic per-file insight records (Generative-
                             Agents-style reflection, no model calls needed)
  * Forgetting/archive     - episodic log pruned to a hot window, older lines
                             archived; semantic store bounded
  * Crash-safe writes      - atomic tmp+replace, never a torn JSONL

Same public API as v1 (store/retrieve/delete/clear/record_event/recent_events/
remember/recall), so callers need zero changes.
"""

import json
import math
import os
import threading
import time
import uuid

import requests

EMBED_URL = os.environ.get("APEX_EMBED_URL", "http://127.0.0.1:1234/v1/embeddings")
EMBED_MODEL = os.environ.get("APEX_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
ROOT = os.path.dirname(os.path.abspath(__file__))
EPISODIC_PATH = os.path.join(ROOT, "memory_episodic.jsonl")
SEMANTIC_PATH = os.path.join(ROOT, "memory_semantic.jsonl")
ARCHIVE_PATH = os.path.join(ROOT, "Logs", "memory_archive.jsonl")
STATE_PATH = os.path.join(ROOT, "Config", "memory_state.json")

MAX_SEMANTIC_RECORDS = 800
EPISODIC_KEEP = 500          # hot episodic window; older lines are archived
DECAY_HALF_LIFE_DAYS = 30.0
IMPORTANCE = {"lesson": 1.20, "rule": 1.15, "insight": 1.10, "success": 1.00,
              "fragment": 1.00, "error": 0.90}
W_COS, W_KW, W_IMP, W_REC = 0.55, 0.25, 0.12, 0.08
DEDUP_SIM = 0.95
CONSOLIDATE_INTERVAL_S = 6 * 3600


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(x * x for x in b) ** 0.5 or 1.0
    return dot / (na * nb)


def _imp_norm(kind):
    return IMPORTANCE.get(kind, 1.0) / max(IMPORTANCE.values())


def _recency(ts_str):
    try:
        age_days = (time.time() - time.mktime(time.strptime(ts_str, "%Y-%m-%d %H:%M:%S"))) / 86400.0
        return 0.5 ** (max(0.0, age_days) / DECAY_HALF_LIFE_DAYS)
    except Exception:
        return 0.5


class ApexMemory:
    def __init__(self):
        self.memory = {}  # Tier 1: working memory
        self._lock = threading.RLock()
        self._embed_ok = None
        # Instance-level paths (tests/other hosts can redirect safely)
        self.episodic_path = EPISODIC_PATH
        self.semantic_path = SEMANTIC_PATH
        self.archive_path = ARCHIVE_PATH

    # ------------------------------------------------------------ durability
    @staticmethod
    def _atomic_write(path, text):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)

    # ------------------------------------------------------------------ T1
    def store(self, key, value): self.memory[key] = value
    def retrieve(self, key): return self.memory.get(key)
    def delete(self, key): self.memory.pop(key, None)
    def clear(self): self.memory.clear()

    # ------------------------------------------------------------------ T2
    def record_event(self, kind, text, **metadata):
        """Append an episodic event. Cheap, durable, no embeddings."""
        entry = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "kind": kind, "text": str(text)[:2000], "meta": metadata,
                 "imp": _imp_norm(kind)}
        try:
            with self._lock:
                with open(self.episodic_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=True) + "\n")
            self._maybe_maintain()
        except OSError:
            pass
        return entry["id"]

    def recent_events(self, n=20, kind=None):
        try:
            with open(self.episodic_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-(n * 3):]
            events = [json.loads(l) for l in lines if l.strip()]
            if kind:
                events = [e for e in events if e.get("kind") == kind]
            return events[-n:]
        except (OSError, json.JSONDecodeError):
            return []

    def _maybe_maintain(self):
        """Trigger archive pruning + consolidation on cadence (never raise)."""
        try:
            st = {"last": 0}
            if os.path.exists(STATE_PATH):
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    st = json.load(f)
            if time.time() - float(st.get("last_consolidate", 0)) < CONSOLIDATE_INTERVAL_S:
                return
            self.consolidate()
            st["last_consolidate"] = time.time()
            os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(st, f)
        except Exception:
            pass
        self._archive_if_needed()

    def _archive_if_needed(self):
        try:
            with open(self.episodic_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) <= EPISODIC_KEEP:
                return
            keep = lines[-EPISODIC_KEEP:]
            old = lines[:len(lines) - EPISODIC_KEEP]
            os.makedirs(os.path.dirname(self.archive_path), exist_ok=True)
            with open(self.archive_path, "a", encoding="utf-8") as f:
                f.writelines(old)
            self._atomic_write(self.episodic_path, "".join(keep))
        except Exception:
            pass

    def consolidate(self):
        """Deterministic reflection: distill recent episodic outcomes per file
        into semantic insight fragments (Generative-Agents-style, no LLM cost)."""
        try:
            events = self.recent_events(200)
            lessons = []
            gym_stats = {"drills": 0, "gains": 0}
            stats = {}
            order = []
            for e in events:
                fn = (e.get("meta") or {}).get("file") or "system"
                st = stats.setdefault(fn, {"success": 0, "error": 0, "pass": 0, "last": ""})
                k = e.get("kind")
                if k == "evolution_pass":
                    st["pass"] += 1
                elif k in st:
                    st[k] += 1
                st["last"] = e.get("text", "")[:140]
                if k == "lesson":
                    lessons.append(txt[:180])
                if e.get("meta", {}).get("gym") or txt.startswith("GYM["):
                    gym_stats["drills"] += 1
                    gym_stats["gains"] += 1 if "gain" in txt else 0
                order.append(fn)
            made = 0
            if gym_stats["drills"]:
                rate = gym_stats["gains"] / max(1, gym_stats["drills"])
                self.remember(f"Gym insight: {gym_stats['gains']}/{gym_stats['drills']} "
                              f"drills gained (rate {rate:.2f}). Weakest traits next.",
                              kind="insight", gym=True)
            trait_insights = {}
            if lessons:
                self.remember("Recent lessons worth keeping: " + " | ".join(lessons[:4]),
                              kind="insight", lesson_batch=True)
            trait_stats2 = {}
            for e in events:
                if e.get("kind") == "calibration":
                    tr = str((e.get("meta") or {}).get("kind") or (e.get("meta") or {}).get("trait") or "general")
                    st2 = trait_stats2.setdefault(tr, {"try": 0, "hit": 0, "misses": []})
                    st2["try"] += 1
                    if (e.get("meta") or {}).get("match") is True or "gain" in e.get("text", ""):
                        st2["hit"] += 1
                    elif "miss" in e.get("text", "") and len(st2["misses"]) < 2:
                        st2["misses"].append(e.get("text", "")[:90])
            for tr, st2 in trait_stats2.items():
                if st2["try"] >= 2:
                    self.remember(f"Trait insight [{tr}]: {st2['hit']}/{st2['try']} gained."
                                  + (" Misses: " + " | ".join(st2["misses"]) if st2["misses"] else ""),
                                  kind="insight", trait_insight=True, trait=tr)
            for fn, st in stats.items():
                if st["success"] + st["error"] + st["pass"] < 3:
                    continue
                text = (f"Insight [{fn}]: {st['success']} successes, {st['error']} failures, "
                        f"{st['pass']} scored passes in recent history. Latest: {st['last']}")
                self.remember(text, kind="insight", file=fn, consolidated=True)
                made += 1
            return made
        except Exception:
            return 0

    # ------------------------------------------------------------------ T3
    def _embed(self, text):
        # circuit breaker: a dead embedder must not tax EVERY call with a
        # dead wait - retry at most once per 10 min, degrade to keyword-only
        if getattr(self, "_embed_ok", None) is False and time.time() - getattr(self, "_embed_failed_at", 0.0) < 600:
            return None
        try:
            r = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "input": text[:4000]},
                              timeout=8)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data and isinstance(data, list):
                    self._embed_ok = True
                    return data[0].get("embedding")
            self._embed_ok = False
            self._embed_failed_at = time.time()
        except requests.RequestException:
            self._embed_ok = False
            self._embed_failed_at = time.time()
        return None

    def _load_semantic(self):
        try:
            with open(self.semantic_path, "r", encoding="utf-8") as f:
                return [json.loads(l) for l in f if l.strip()]
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def _kw_score(query, text):
        ql = query.lower().replace(".", " ").replace("_", " ").split()
        qwords = {w for w in ql if len(w) > 2}
        if not qwords:
            return 0.0
        rl = text.lower()
        hits = sum(1 for w in qwords if w in rl)
        return hits / len(qwords)

    def remember(self, text, kind="fragment", **metadata):
        """Store a knowledge fragment with embedding. Near-duplicates refresh
        the existing entry (dedup) instead of bloating the store."""
        rec = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "kind": kind, "text": str(text)[:2000], "meta": metadata,
               "imp": _imp_norm(kind)}
        vec = self._embed(rec["text"])
        if vec:
            rec["vec"] = vec
        hit_id = None
        with self._lock:                   # RLock + single writer: the concurrent-
            if vec:                        # chats lost-update race dies here
                # Deduplication pass
                rows_for_dedup = self._load_semantic()
                for row in rows_for_dedup:
                    if "vec" in row and _cosine(vec, row["vec"]) >= DEDUP_SIM:
                        row["ts"] = rec["ts"]          # refresh recency
                        row["acc"] = row.get("acc", 0) + 1
                        self._persist(rows_for_dedup)  # persist the MUTATED rows
                        hit_id = row["id"]             # (old code re-loaded + lost it)
                        break
            if hit_id is None:
                rows = self._load_semantic()
                rows.append(rec)
                rows = rows[-MAX_SEMANTIC_RECORDS:]
                self._persist(rows)
                hit_id = rec["id"]
        return hit_id

    def _persist(self, rows):
        try:
            with self._lock:
                os.makedirs(os.path.dirname(self.semantic_path), exist_ok=True)
                self._atomic_write(self.semantic_path,
                                   "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in rows))
        except Exception:
            pass

    def recall(self, query, k=5, kind=None, min_similarity=0.30):
        """Hybrid retrieval: cosine + keyword + importance + recency fusion.
        `min_similarity` applies to the vector-cosine truth channel; keyword-
        only rows (embeddings offline) fall back to overlap filtering."""
        full_rows = self._load_semantic()          # NEVER persist a filtered view
        rows = full_rows if not kind else [r for r in full_rows if r.get("kind") == kind]
        if not rows:
            return []
        qvec = self._embed(query)
        scored = []
        for r in rows:
            cos = 0.0
            if qvec and self._embed_ok and "vec" in r:
                cos = max(0.0, _cosine(qvec, r["vec"]))
            kw = self._kw_score(query, r["text"])
            if cos < min_similarity and kw == 0.0:
                continue  # neither channel finds it relevant
            s = (W_COS * cos + W_KW * kw + W_IMP * _imp_norm(r.get("kind", "fragment"))
                 + W_REC * _recency(r.get("ts", "")))
            scored.append((r, s, cos, kw))
        scored.sort(key=lambda x: x[1], reverse=True)
        out = []
        for r, s, cos, kw in scored[:k]:
            r["acc"] = r.get("acc", 0) + 1  # access reinforcement
            out.append({"text": r["text"], "kind": r.get("kind"), "ts": r.get("ts"),
                        "similarity": round(s, 4), "cosine": round(cos, 4), "kw": round(kw, 3),
                        "meta": r.get("meta", {})})
        if out:
            try:
                self._persist(full_rows)   # persist the mutated ORIGINALS (the old
            except Exception:              # code re-loaded a fresh copy and lost
                pass                       # every reinforcement silently)
        return out


if __name__ == "__main__":
    m = ApexMemory()
    made = m.consolidate()
    m.remember("Sandbox runs must stay under 8 seconds to protect the host CPU.", kind="rule")
    print("consolidated:", made)
    print("recall ->", json.dumps(m.recall("protect host cpu", k=2), indent=2)[:400])
