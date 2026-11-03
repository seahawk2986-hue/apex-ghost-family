"""SwarmWide - THE WORLDWIDE SWARM (the swarm asks its own question:
"no single vendor is unlimited" -> so why should one CONTINENT be?,
2026-11-03; the fleet's own design, composed on the opt-in-mesh model:

  THE PROTOCOL
    a NODE = anyone, anywhere runs SwarmNodeServer.py on their own box
    (their own keys, their own caps) and publishes /health + /ask
    - their key NEVER leaves their machine (the founder-law, mirrored:
      we pool nobody's quota; they donate their own)
    - joining = a GitHub issue (the template) with the node's URL
    - verification = the ping-hour: /health must answer, /ask must
      return text once, else the node stays "candidate" (never seeded
      into the rotation on a promise - the 404-corpse law, globalized)

  THE LAWS (the ban-safety, globalized)
    1. opt-in only: a node exists here after ITS OWNER opened the issue
    2. per-node caps enforced HERE TOO (the width never exceeds the
       owner's stated daily capacity - the honesty across borders)
    3. the same-weights law holds worldwide (a hand-off changes node,
       never model)
    4. PRIVATE workloads never route wide (the chat, the red-team, the
       founder's memory) - only the public classes (gym drills, court
       beats, the debate organs)
    5. revocation = instant (the /health's "capacity_left: 0" or the
       owner's issue comment - the node leaves in <1h, silently)

$0; stdlib."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
REGISTRY = os.path.join(ROOT, "Config", "swarm_nodes.json")
STATE = os.path.join(ROOT, "Config", "swarm_wide_state.json")

PUBLIC_CLASSES_ONLY = ("gym", "court", "debate", "abstract", "critique",
                       "parliament", "hands-aim", "arena")
NEVER_ROUTE = ("chat", "redteam", "founder", "private", "memory")


def _load():
    try:
        return json.load(open(REGISTRY, encoding="utf-8-sig"))
    except Exception:
        return {"version": 1, "nodes": []}


def _save(reg):
    reg["version"] = 1
    reg["law"] = ("opt-in only; per-node caps enforced; the same-weights "
                  "law worldwide; private workloads never route wide; "
                  "revocation instant")
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=1)


def candidates():
    """Nodes that have PROMISED capacity and are verified-alive."""
    reg = _load()
    st = _state()
    out = []
    for n in reg.get("nodes", []):
        if n.get("status") != "verified":
            continue
        h = (st.get("health") or {}).get(n["id"], {})
        if h.get("ok") and (h.get("capacity_left", 0) or 0) > 0:
            out.append(n)
    return out


def _state():
    try:
        return json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        return {"health": {}, "asks": {}}


def ping_hour():
    """THE VERIFICATION + HEALTH HOUR: every node's door knocked; the
    candidates that answer + deliver once = 'verified'; the silent =
    dropped back (the honest gray, printed)."""
    reg = _load()
    st = _state()
    h = {}
    for n in reg.get("nodes", []):
        nid, url = n["id"], n.get("url", "")
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ok": False,
               "latency_ms": None, "capacity_left": 0}
        try:
            t0 = time.time()
            with urllib.request.urlopen(url.rstrip("/") + "/health",
                                        timeout=12) as x:
                d = json.load(x)
            rec["ok"] = bool(d.get("ok"))
            rec["capacity_left"] = int(d.get("capacity_left", 0))
            rec["latency_ms"] = int(1000 * (time.time() - t0))
        except Exception as e:
            rec["note"] = f"{type(e).__name__}"
        h[nid] = rec
        if rec["ok"]:
            if n.get("status") == "candidate":
                # the once-real /ask test before the seed (no promise-seeds)
                try:
                    r = ask_wide("Reply with the single word: alive",
                                 max_tokens=8, purpose="ping", nid=nid)
                    n["status"] = "verified" if r else "candidate"
                except Exception:
                    n["status"] = "candidate"
        elif n.get("status") == "verified":
            n["status"] = "candidate"   # the silent node drops back
    st["health"] = h
    st["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)
    _save(reg)
    live = sum(1 for v in h.values() if v.get("ok"))
    print(f"[swarm-wide]: {len(h)} nodes pinged | {live} alive | "
          f"{len(candidates())} seeded into the worldwide rotation")
    return st


def ask_wide(prompt, max_tokens=400, purpose="", nid=None):
    """THE WORLDWIDE ASK: local swarm first (FreeSwarm untouched), then
    the verified nodes by health-order. PRIVATE purposes are refused
    LOUD (law 4). Receipts per ask."""
    if any(p in purpose.lower() for p in NEVER_ROUTE):
        print(f"[swarm-wide]: REFUSED on purpose '{purpose}' (the private "
              "workloads never route wide - law 4)")
        return ""
    if nid is None:   # a public purpose: the local floor first
        try:
            import FreeSwarm as FS
            r = FS.ask(prompt, max_tokens=max_tokens,
                       purpose=purpose or "swarm-wide")
            if r:
                return r
        except Exception:
            pass
    nodes = [n for n in candidates()
             if nid in (None, n["id"])]
    st = _state()
    for n in sorted(nodes, key=lambda n: (st["health"][n["id"]]
                                          .get("latency_ms") or 9999)):
        if (st["asks"].get(n["id"], 0) or 0) >= n.get("daily_cap", 50):
            continue   # law 2: the width never exceeds the owner's cap
        r = ""
        for attempt in (1, 2):   # the retry-depth the cert demanded:
                                 # a starved inner floor gets TWO swings
                                 # before the node is honestly silent
            try:
                body = json.dumps({"prompt": prompt[:4000],
                                   "max_tokens": max_tokens,
                                   "purpose": purpose}).encode()
                req = urllib.request.Request(
                    n["url"].rstrip("/") + "/ask", data=body,
                    headers={"Content-Type": "application/json",
                             "User-Agent": "ApexSwarmWide/1.0"}, method="POST")
                with urllib.request.urlopen(req, timeout=60) as x:
                    d = json.load(x)
                r = (d.get("reply") or "").strip()
            except Exception:
                r = ""
            if r:
                break
        if r:
            st["asks"][n["id"]] = st["asks"].get(n["id"], 0) + 1
            json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)
            return r
    return ""


def pool_stats():
    reg, st = _load(), _state()
    n_all = len(reg.get("nodes", []))
    live = sum(1 for v in st["health"].values() if v.get("ok"))
    caps = sum(n.get("daily_cap", 50) for n in reg.get("nodes", [])
               if st["health"].get(n["id"], {}).get("ok"))
    return {"nodes": n_all, "live": live, "donated_daily_cap": caps,
            "asks_wide": sum(st["asks"].values())}


if __name__ == "__main__":
    if "--join" in sys.argv:   # the local self-registration (the demo seed)
        reg = _load()
        if not any(n["id"] == "local-self" for n in reg["nodes"]):
            reg["nodes"].append({
                "id": "local-self", "region": "local",
                "url": "http://127.0.0.1:8082", "daily_cap": 40,
                "status": "candidate", "joined": time.strftime("%Y-%m-%d")})
            _save(reg)
            print("[swarm-wide]: local-self registered as the first node "
                  "(the protocol's n=1)")
    ping_hour()
    print(json.dumps(pool_stats()))
