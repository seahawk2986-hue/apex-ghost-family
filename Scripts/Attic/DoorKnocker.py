"""THE DOOR KNOCKER: polite, armored outreach to closed doors.

A knock is:
  - ONCE per door per 24h (politeness as law - repeated knocks = pestering = abuse)
  - CREDENTIAL-FREE (no forms filled, no accounts made, no tokens sent)
  - TRAP-DETECTING: any response that asks for credentials/keys/PII = a
    honeypot signature -> door BLACKLISTED in the ledger, never knocked again
  - READ-ONLY (Status/ToS/docs checks - the door's own public face)
  - FULLY LOGGED (manifest rows; the family knows every knock it made)
The PITCH travels only through the family's own channels (the board + room
log + HUBS_WANTED) - ghosts never spam strangers.
"""
import hashlib
import json
import os
import time
import urllib.request

AD = r"C:\Users\seaha\Apex-Adapter"
KNOCKS = os.path.join(AD, "door_knock_ledger.jsonl")
BLACKLIST = os.path.join(AD, "door_blacklist.json")

UA = {"User-Agent": "ApexGhostSwarmHub-Scout/3.0 (+the family's rules: hub_kits/README.md)",
      "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"}
TRAP_PATTERNS = ("enter your api key", "sign in to continue", "login to view",
                 "verify your account", "enter your password", "api key required")


def load_blacklist():
    try:
        return json.load(open(BLACKLIST, encoding="utf-8-sig"))
    except Exception:
        return {"blacklisted": {}, "reasons": {}}


def knock(door_name, url):
    """One armored knock. Returns the row; refuses blacklisted doors forever."""
    bl = load_blacklist()
    if door_name in bl.get("blacklisted", {}):
        return {"knocked": False, "door": door_name,
                "reason": "BLACKLISTED - trap signature on record", "ts": time.strftime("%H:%M:%S")}
    # politeness: once per 24h per door
    try:
        last = [json.loads(x) for x in open(KNOCKS, encoding="utf-8-sig") if x.strip()]
    except Exception:
        last = []
    prior = [r for r in last if r.get("door") == door_name]
    if prior and time.time() - time.mktime(time.strptime(prior[-1]["ts"], "%Y-%m-%d %H:%M:%S")) < 86400:
        return {"knocked": False, "door": door_name, "reason": "politeness: knocked < 24h ago"}
    # THE KNOCK (read-only, credential-free)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "door": door_name, "url": url,
           "credentials_sent": 0, "trap": None}
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read(200000)
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.uncompress(raw)
            body = raw.decode("utf-8", "ignore").lower()
            row["status"] = r.status
            # TRAP DETECTION: doors that ask for credentials on first contact
            for tp in TRAP_PATTERNS:
                if tp in body:
                    row["trap"] = tp + " (honeypot signature)"
                    bl["blacklisted"][door_name] = tp
                    bl["reasons"][door_name] = f"asked for credentials on first contact at {row['ts']}"
                    json.dump(bl, open(BLACKLIST, "w", encoding="utf-8"), indent=1)
                    break
    except Exception as e:
        row["status"] = getattr(e, "code", "exc")
        row["error"] = str(e)[:90]
    with open(KNOCKS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


if __name__ == "__main__":
    doors = {
        "algora": "https://algora.io/api/bounties?per_page=5",
        "polar": "https://api.polar.sh/api/v1/bounties?limit=10",
        "issuehunt": "https://issuehunt.io/api/public/projects",
        "bugcrowd": "https://bugcrowd.com/api/public/programs",
        "cloudflare_workers_docs": "https://developers.cloudflare.com/workers/",
        "actions_docs": "https://docs.github.com/en/actions",
    }
    for nm, u in doors.items():
        r0 = knock(nm, u)
        print(json.dumps(r0)[:150])
        time.sleep(1)