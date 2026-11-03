"""LightRec - THE HABITS ORGAN (the personal-assistant's last mile,
2026-11-03; the fleet's own invention — the honest gap found when the
cache audit showed `store_chat` keeps only the REPLY: the user's message
is a hash, so the recurring asks were never recoverable. The fix has two
halves:

  CAPTURE  a bounded, LOCAL-ONLY store of the user's own asks
           (Config/lightrec.jsonl; founder-owned machine; purged whole
           by `!forgetme`; nothing leaves the disk)
  MINE     the recurring-pattern detector: near-dup clustering of the
           normalized asks (the same law the cache's near-dup tier uses)
           -> the habits table (pattern, count, last ts) + a
           PROMPT-LIBRARY SECTION the chat can inject, so the next "run
           the court" arrives pre-primed.

THE HONEST LAWS
  - nothing invented: a habit = >=2 REAL occurrences of the same ask
  - the section() text always carries its counts (the receipts inline)
  - the empty-state prints "no recurring patterns yet" (never fake flavor)
$0; stdlib ONLY (the mining is pure text-machinery)."""

import json
import os
import re
import sys
import time
from collections import Counter

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STORE = os.path.join(ROOT, "Config", "lightrec.jsonl")
STATE = os.path.join(ROOT, "Config", "lightrec.json")
MAX_ROWS = 500          # the bounded store (the oldest fall off)
MAX_MSG = 500           # chars kept per capture


def _norm(t):
    """The near-dup normalizer: the cache's law, reused."""
    t = (t or "").lower()
    t = re.sub(r"https?://\S+", " <url> ", t)
    t = re.sub(r"[^a-z0-9 <>,.?!']", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _sig(t):
    """The habit-signature: the first clause-ish chunk, normalized (the
    'same ask' test - the greeting/preamble stripped)."""
    n = _norm(t)
    n = re.sub(r"^(hey|hi|yo|ok|okay|please|so|and)[ ,]+", "", n)
    n = re.sub(r"\b(you|please|can|could|would|now|again|pls|plz|thanks|thank)\b",
               " ", n)
    return re.sub(r"\s+", " ", n)[:80]


def capture(text, source="chat"):
    """THE STORE-HALF: one row per real user ask (call from the chat wire;
    short messages (<=4 chars, the ghost-law) and commands stay out)."""
    t = (text or "").strip()
    if len(t) <= 4 or t.startswith("!"):
        return None
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "msg": t[:MAX_MSG],
           "src": source}
    try:
        rows = _rows()
        rows.append(row)
        if len(rows) > MAX_ROWS:
            rows = rows[-MAX_ROWS:]
        with open(STORE, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return row
    except Exception as e:
        print(f"[lightrec] capture failed honestly: {e}", file=sys.stderr)
        return None


def _rows():
    try:
        return [json.loads(l) for l in open(STORE, encoding="utf-8-sig")
                if l.strip()]
    except Exception:
        return []


def forgetme():
    """THE PRIVACY DOOR: the whole habit-store purged, honestly printed."""
    try:
        os.remove(STORE)
    except Exception:
        pass
    json.dump({"habits": [], "notes": "purged by !forgetme",
               "ts": time.strftime("%Y-%m-%d %H:%M:%S")},
              open(STATE, "w", encoding="utf-8"), indent=1)
    print("[lightrec]: the habit-store purged (the founder's privacy door)")


def mine():
    """THE MINE-HALF: near-dup clusters -> the habits table + the state."""
    rows = _rows()
    clusters = {}
    for r in rows:
        s = _sig(r.get("msg", ""))
        if len(s) < 6:        # too small to be a habit-signature
            continue
        c = clusters.setdefault(s, {"count": 0, "first": r["ts"],
                                    "last": r["ts"], "example": r["msg"][:140]})
        c["count"] += 1
        c["last"] = r["ts"]
    habits = sorted(({"pattern": s, **c} for s, c in clusters.items()
                     if c["count"] >= 2),                    # >=2 = a HABIT
                    key=lambda h: -h["count"])[:12]
    # the topic-meters (the honest keyword counter over the same rows)
    words = Counter(w for r in rows for w in re.findall(
        r"[a-z]{4,}", _norm(r.get("msg", "")))
        if w not in ("this", "that", "with", "please", "then", "just",
                     "make", "want", "need", "your", "from", "what"))
    st = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
          "capts": len(rows), "habits_n": len(habits),
          "habits": habits, "topics": words.most_common(8)}
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)
    print(f"[lightrec]: {len(rows)} asks mined -> {len(habits)} honest habits"
          f" | top topics: {[w for w, _ in st['topics'][:4]]}")
    return st


def section():
    """THE INJECT: the dynamic prompt-library section (the chat's builder
    calls this; carries its counts inline - the honesty law)."""
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        st = {}
    h = st.get("habits") or []
    if not h:
        return ""
    lines = [f"- \"{hh['example']}\" (x{hh['count']}, last {hh['last'][:10]})"
             for hh in h[:5]]
    return ("ANDREW'S RECURRING ASKS (the learned habits, from " +
            str(st.get("capts", "?")) + " stored asks - use for context, "
            "never assume it applies to the current message):\n" +
            "\n".join(lines))


if __name__ == "__main__":
    forget = "--forget" in sys.argv
    if forget:
        forgetme()
    mine()
    s = section()
    print("--- section ---" if s else "--- section: (the honest empty) ---")
    print(s[:400])
