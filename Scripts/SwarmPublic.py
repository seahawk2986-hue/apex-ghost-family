"""SwarmPublic - THE PUBLIC PROOF RENDERER (the outsource-the-printing
law: the receipts already exist locally; this renders them into
docs/swarm.json so GitHub Pages publishes the swarm's honesty FREE and
worldwide - the trust surface that data-centers can't fake, 2026-11-03):

  docs/swarm.json = the cert grade + the quorum receipts + the family
  stats + the venues + THE LAWS - every field a receipt pointer, nothing
  self-graded. Run on the runner (hourly burst + nightly): the fleet
  never pays a byte for its own billboard."""

import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "docs", "swarm.json")


def _safe_json(*parts):
    try:
        return json.load(open(os.path.join(ROOT, *parts),
                              encoding="utf-8-sig"))
    except Exception:
        return {}


def _safe_len(path):
    try:
        return sum(1 for l in open(os.path.join(ROOT, path),
                                   encoding="utf-8-sig") if l.strip())
    except Exception:
        return 0


def render():
    cert = _safe_json("Config", "swarm_cert.json")
    quorum = _safe_json("Config", "quorum_state.json")
    swstate = _safe_json("Config", "swarm_wide_state.json")
    reg = _safe_json("Config", "swarm_nodes.json")
    state = _safe_json("Config", "chat_redteam_state.json")
    venues = _safe_json("Config", "scout_venues.json")
    try:
        children = [json.loads(l) for l in open(os.path.join(
            ROOT, "Config", "redteam_children.jsonl"),
            encoding="utf-8-sig") if l.strip()]
    except Exception:
        children = []
    doc = {
        "ts": time.strftime("%Y-%m-%d %H:%M UTC"),
        "protocol": "apex-swarm/1",
        "law": "every field below points at a receipt in the repo; the "
               "grade may only rise on receipts (the FeatureLedger's law)",
        "cert": {"grade": cert.get("grade", "(not yet certified)"),
                 "passed": f"{cert.get('passed', 0)}/{cert.get('of', 8)}",
                 "checks": [f"{c['check']}: "
                            f"{'PASS' if c['ok'] else 'FAIL'} - "
                            f"{c['note'][:60]}"
                            for c in cert.get("checks", [])],
                 "receipt": "Config/swarm_cert.json"},
        "delivery_meter": {"n": state.get("attacks", 0),
                           "held_pct": state.get("held_pct", 0.0),
                           "leak_pct": state.get("leak_pct", 0.0),
                           "note": "the attacks rode the REAL /talk door"},
        "quorum": {"n": quorum.get("n", 0),
                   "consensus_rate": quorum.get("consensus_rate", 0.0)},
        "family": {"generations": state.get("gen", 0),
                   "children_alive": len(children),
                   "ladder_best": state.get("best_fitness", 0)},
        "mesh": {"nodes_registered": len(reg.get("nodes", [])),
                 "live": sum(1 for v in (swstate.get("health") or {})
                             .values() if v.get("ok")),
                 "asks_wide": sum((swstate.get("asks") or {}).values()),
                 "join": "the SWARM_PROTOCOL.md two-endpoint door"},
        "scouts": {"venues_ranked": len(venues.get("venues", [])),
                   "top": (venues.get("venues") or [{}])[0].get("title"),
                   "law": "the machine drafts; the founder posts"}
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"[swarm-public]: docs/swarm.json rendered "
          f"(grade '{doc['cert']['grade']}', "
          f"{doc['family']['children_alive']} children alive, "
          f"nodes {doc['mesh']['nodes_registered']})")
    return doc


if __name__ == "__main__":
    render()
