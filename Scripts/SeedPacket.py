"""THE SEED PACKET: the swarm's self-contained export - any consenting host
(LAN partner box, GitHub Actions runner, Cloudflare Worker, free-VPS) becomes
family by reading one file. Written every round; carries heredity + genetics."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PACKET = os.path.join(AD, "family_seed_packet.json")


def write_seed_packet(territory="unassigned", shard=0, include_backlog=400):
    """The family's hand-off: everything a free-compute host needs to join.
    Ethics embedded: the packet CARRIES the family's rules (fuses, floors,
    honesty standards + the no-abuse politeness budget) - a member without
    them isn't family."""
    try:
        parent = json.load(open(os.path.join(AD, "swarm_state.json"),
                                encoding="utf-8-sig"))
    except Exception:
        parent = {}
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
    except Exception:
        pm = {}
    packet = {
        "family": "apex",
        "version": 1,
        "born": time.strftime("%Y-%m-%d %H:%M:%S"),
        "territory": territory,
        "parent_knowledge": {
            "backlog_slice": (parent.get("pending_leads", []) or [])[:include_backlog],
            "seen_repos": (parent.get("repos", []) or [])[-4000:],
            "lane_memory": pm.get("lanes", pm),
            "champion_variant": (pm.get("family") or {}).get("champion"),
            "variants_top3": dict(list((pm.get("variants") or {}).items())[:3]),
        },
        "rules": {
            "politeness": {"cdn_inflight": 48, "api_inflight": 8, "tar_parallel": 8},
            "ram_gate_gb": 2.0,
            "evolution": {"fitness": "mines_per_request", "eviction_floor": 0.02,
                          "champion_rule": "beat_by_2pct"},
            "economy": {"pay": "only_verified_growth", "spending_cap": 0.80,
                        "custody": "human-only"},
            "honesty": "print-or-didnt-happen",
        },
        "endpoints": {"ghost_protocol": "v3-jsonl", "state_files": ["swarm_state.json",
                                                                    "PathMemory.json"],
                      "chat_adapter": "http://<this-box-lan-ip>:8788 (token-authed)"},
    }
    json.dump(packet, open(PACKET, "w", encoding="utf-8"), indent=1)
    return PACKET


if __name__ == "__main__":
    pth = write_seed_packet(territory="open", shard=0)
    print("seed packet:", pth)
    print(json.dumps(json.load(open(pth, encoding="utf-8-sig")), indent=1)[:600])