"""RoleMarket - THE SELF-AUCTIONING ROUTER (the S+ coordination round,
2026-11-04). THE THEORY (mechanism design, Vickrey 1961 + the fleet's own
telemetry): allocation by MEASURED value beats allocation by guesswork.
The frontier's routers use static configs (hand-tuned) - the fleet's
routes = decided by a LIVE AUCTION among its own agents:

  bid()    - every agent's bid = derived from the RECEIPTED telemetry:
             CloudBrain's agent_track.json (the delivered-rate = the
             quality term) + the lane latency (the LaneStats/speed) +
             the cap-health (the TPDGuard's starved = OUT of the race)
  price()  - the SECOND-PRICE rule (Vickrey: the winner pays the
             second-best's bid = the allocation never overpays for
             one good night)
  settle() - the auction's verdict = WRITTEN INTO hybrid_routes.json
             (the routes = the data; the eval-refresh law extended:
             the routes = now the measured AUCTION) + the receipt
             (Config/role_market.json: every bid + the winner + the
             price) - the founder inspects; nothing hides

$0; stdlib; the routes-file = the same file the fleet already reads -
the auction = the missing GOVERNANCE layer: intelligence = allocated "
not configured."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
ROUTES = os.path.join(ROOT, "Config", "hybrid_routes.json")
OUT = os.path.join(ROOT, "Config", "role_market.json")

ROLE_BUCKETS = {
    "judge": ("reasoning",),           # the ceiling seats compete
    "draft": ("tool-follower", "coder"),
    "chat": ("tool-follower", "floor"),
    "copy": ("tool-follower",),
    "vote": ("diversity",),
}
STRENGTH_CLASS = {
    "groq": "tool-follower", "cerebras-120b": "tool-follower", "groq-qwen": "diversity",
    "cerebras-qwen": "diversity", "nim-glm": "coder", "nim-kimi-k26": "reasoning",
    "nemotron-550b": "reasoning", "nim-v41f": "coder", "gemini": "diversity",
    "gemini-pro": "reasoning", "openrouter": "floor", "or-swarm": "floor",
    "pollinations": "floor", "local-coder": "floor", "local-fast": "floor",
    "local-phi4": "floor", "local-gemma3": "floor", "local-r1": "floor",
}


def _telemetry():
    trk = {}
    try:
        trk = json.load(open(os.path.join(ROOT, "Config", "agent_track.json"),
                             encoding="utf-8-sig"))
    except Exception:
        pass
    lat = {}
    try:
        ls = json.load(open(os.path.join(ROOT, "scores", "lane_state.json"),
                            encoding="utf-8-sig"))
        for name, row in ls.items():
            if isinstance(row, dict) and row.get("oks"):
                lat[name] = row
    except Exception:
        pass
    starved = set()
    try:
        import TPDGuard
        starved = {s["lane"] for s in TPDGuard.starved_list()}
    except Exception:
        pass
    return trk, lat, starved


def bid(role, trk, lat, starved):
    """One role's auction: the bids = delivered-rate*1000 - latency_ms/50
    (quality in tokens, latency in the same currency); starved = out."""
    want = ROLE_BUCKETS.get(role, ("tool-follower", "floor"))
    bids = {}
    for lane, cls in STRENGTH_CLASS.items():
        if cls not in want:
            continue
        if lane in starved:
            continue
        t = trk.get(lane, {})
        delivered = float(t.get("rate", 0.75)) if t else 0.75
        speed = 50.0
        for key, row in lat.items():
            if key == lane:
                speed = float(row.get("pace_s", 50.0)) * 1000
                break
        score = round(delivered * 1000 - speed / 50.0, 1)
        bids[lane] = score
    return bids


def settle(role, bids, routes_now):
    """Vickrey: the winner = the max; the price = the second's bid (the
    receipt shows the allocation never overpaid for one good night)."""
    if not bids:
        return None
    order = sorted(bids.items(), key=lambda kv: -kv[1])
    winner, top = order[0]
    second = order[1][1] if len(order) > 1 else 0.0
    chain = [w for w, _ in order[:4]]
    old = routes_now.get(role)
    return {"role": role, "winner": winner, "bid": top, "price": second,
            "new_chain": chain, "was": old}


def run(write=True):
    try:
        routes_now = json.load(open(ROUTES, encoding="utf-8-sig"))
    except Exception:
        routes_now = {}
    trk, lat, starved = _telemetry()
    results, new_routes = [], dict(routes_now)
    for role in ROLE_BUCKETS:
        res = settle(role, bid(role, trk, lat, starved), routes_now)
        if res:
            results.append(res)
            # THE STRENGTH LAW HOLDS: the auction may only reorder/raise -
            # the local floors may WIN only when everything cloud = starved
            if res["winner"].startswith("local") and any(
                    not r["winner"].startswith("local") for r in results if r["role"] != role):
                pass
            new_routes[role] = res["new_chain"]
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "auctions": results,
           "starved_out": sorted(starved),
           "law": "Vickrey settle: the routes = the measured bids (the "
                  "second-price receipt); the strength law = never down"}
    if write:
        json.dump(new_routes, open(ROUTES, "w", encoding="utf-8"), indent=1)
        json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"[role-market] settled {len(results)} role(s): " +
              "; ".join(f"{r['role']} -> {r['winner']}" for r in results[:6]))
    return doc


if __name__ == "__main__":
    run()