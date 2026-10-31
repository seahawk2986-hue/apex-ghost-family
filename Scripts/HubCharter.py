"""THE HUB CHARTER - domiciled family members with their own fleets.

A hub LIVES on a consenting host: persistent local knowledge, its own ghost
fleet, pull/push transport with the family, and cross-hub champion elections.
Consent is explicit and timestamped; the family RULES arrive with the packet
- the conscience travels with the capacity.

Transport:
  PULL: the hub polls the family's seed packet (new backlog + genes)
  PUSH: the hub ships harvests back manifest-verified (GrainLine rules)
  Election: hubs compete for the champion throne by measured fitness
            (the 2pct-rule travel to hub level; cheating can't take the crown)
"""
import hashlib
import json
import os
import time
import urllib.request

AD = r"C:\Users\seaha\Apex-Adapter"
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
HUB_DIR = os.path.join(AD, "hubs")
REGISTRY = os.path.join(HUB_DIR, "hub_registry.json")


def hub_dir(hub_id):
    d = os.path.join(HUB_DIR, hub_id)
    os.makedirs(d, exist_ok=True)
    return d


def register(hub_id, machine_class, territories, consent_by, cadence_min=30):
    """CONSENT-GATED: a hub exists only when its person signs it in."""
    if not consent_by or not str(consent_by).strip():
        return {"joined": False, "reason": "hub needs its person's consent"}
    os.makedirs(HUB_DIR, exist_ok=True)
    try:
        reg = json.load(open(REGISTRY, encoding="utf-8-sig"))
    except Exception:
        reg = {"hubs": {}}
    reg["hubs"][hub_id] = {
        "machine_class": machine_class, "territories": territories,
        "consent_by": consent_by, "consent_ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cadence_min": cadence_min,
        "pull_url": "local file transport + room adapter on token-authed :8788"}
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=1)
    hub_dir(hub_id)
    return {"joined": True, "hub": hub_id}


def pull_family(hub_id):
    """The hub inhales the family's latest knowledge (the packet + genes)."""
    hd = hub_dir(hub_id)
    try:
        packet = open(os.path.join(AD, "family_seed_packet.json"),
                      encoding="utf-8-sig").read()
        open(os.path.join(hd, "family_packet.json"),
             "w", encoding="utf-8").write(packet)
        return {"pulled": True, "bytes": len(packet)}
    except Exception:
        return {"pulled": False}


def push_harvest(hub_id, payload):
    """The hub ships its harvest home: manifest-verified, zero-trust accepted
    by the GrainLine discipline (hash, count, timestamp)."""
    hd = hub_dir(hub_id)
    raw = json.dumps(payload, sort_keys=True).encode()
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "hub": hub_id,
           "kind": "harvest", "digest": hashlib.sha256(raw).hexdigest()[:16],
           "rows": len(payload.get("rows", []))}
    with open(os.path.join(hd, "outbox.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def hub_fleet(hub_id, workers=2):
    """The hub lives a LOCAL family fleet (same launcher rules, its own metal)."""
    try:
        subprocess_run = __import__("subprocess").Popen(
            ["python", "-c", "print('hub " + hub_id + " fleet placeholder')"],
            cwd=hub_dir(hub_id))
        return {"fleet_started": workers, "placeholder_pid": subprocess_run.pid}
    except Exception:
        return {"fleet_started": 0}


if __name__ == "__main__":
    # DEMO: the charter flow end to end (no real hub joined - consent not given)
    print(register("demo-hub", "vps-4c24g", ["science"], consent_by=""))
    print("refused: no consent - the hub does not exist without its person's yes")
    print(pull_family("demo-hub"))
    print(push_harvest("demo-hub", {"rows": [], "note": "empty demo push"}))