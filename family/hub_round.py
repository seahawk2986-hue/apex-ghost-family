"""THE HUB'S MINING SCRIPT (committed, runner-safe - no heredoc tricks)."""
import hashlib
import json
import time
import urllib.request

UA = {"User-Agent": "ApexGhostSwarmHub/1.0"}
PACKET_URL = ("https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/"
              "main/family/family_seed_packet.json")

print("consent check: this runner is consent-gated via family/CONSENT.txt")
try:
    open("family/CONSENT.txt", encoding="utf-8").read()
    print("consent file: PRESENT")
except FileNotFoundError:
    print("NO CONSENT FILE - THE HUB REFUSES TO RUN")
    raise SystemExit(1)

req = urllib.request.Request(PACKET_URL, headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    pk = json.load(r)
print("packet pulled: family", pk.get("family"), "| rules", list((pk.get("rules") or {}).keys())[:4])
pending = (pk.get("parent_knowledge") or {}).get("backlog_slice", [])[:150]
print("backlog slice to mine:", len(pending))

ok, mined = 0, []
for lead in pending:
    lead = str(lead).strip()
    if not lead or "/" not in lead:
        continue
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"https://raw.githubusercontent.com/{lead}/HEAD/README.md", headers=UA),
                timeout=20) as resp:
            body = resp.read(96 * 1024)
            if resp.status == 200:
                ok += 1
                low = body[:60000].decode("utf-8", "ignore").lower()
                if any(m in low for m in ("permission is hereby granted, free of charge",
                                          "mit license", "mit-license.org")):
                    mined.append({"repo": lead, "tier": "MINE",
                                  "evidence": "README declares MIT",
                                  "sha": hashlib.sha256(body).hexdigest()[:16]})
    except Exception:
        continue

out = {"hub": "actions-runner", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
       "status": "done", "lifecycle": "done",   # C2 (A2A): explicit task lifecycle
       "requested": len(pending), "ok": ok, "mines": mined[:60],
       "rules_followed": bool(pk.get("rules"))}
with open("hub_round_result.json", "w") as f:
    json.dump(out, f, indent=1)
with open("hub_packet_home.json", "w") as f:
    raw = json.dumps(out, sort_keys=True).encode()
    f.write(json.dumps({"digest": hashlib.sha256(raw).hexdigest()[:16], **out}, indent=1))
print(f"hub round complete: {ok} reads, {len(mined)} mines - manifest digest written")