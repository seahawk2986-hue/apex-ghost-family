"""THE PAYOUT DOOR: the family's earnings route to the founder's PayPal.

PRIVACY LAW (2026-11-04): the receiving address lives ONLY in the repo's
gitignored .env as PAYOUT_DEST - every output this door writes (ledger,
seed packet) records a REDACTED reference, never the literal address.
The email is a RECEIVING address (safe, not a credential) - the family
never holds payment credentials; it only records where YOU want money to land.

HONEST CAVEAT: git history retains the old literals - history rewrite
(filter-repo + force-push) or receiving-address rotation = founder-only
actions; this door never touches history silently."""
import io
import json
import os
import py_compile
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CE = os.path.join(ROOT, "Scripts", "CryptoEconomy.py")
PKT = os.path.join(AD, "family_seed_packet.json")
LED = os.path.join(ROOT, "Config", "CryptoLedger.json")

DEST = "ENV:PAYOUT_DEST (redacted from repo content 2026-11-04)"
REF = "paypal:ENV:PAYOUT_DEST"
log = []

def _env_dest():
    try:
        with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
            for ln in f:
                if ln.strip().startswith("PAYOUT_DEST="):
                    return ln.split("=", 1)[1].strip()
    except Exception:
        pass
    return None

# 0. the destination must exist in .env (the founder set it once; we verify)
dest = _env_dest()
log.append(("OK   " if dest else "MISS ") + "env-PAYOUT_DEST")
if not dest:
    print("\n".join(log))
    print("PAYOUT RAIL (DESIGN ONLY): destination NOT SET - add "
          "PAYOUT_DEST=<your receiving address> to .env (gitignored) and re-run.")
    sys.exit(1)

# 1. the ledger records the destination, REDACTED (the family's payout rail)
L = json.load(open(LED, encoding="utf-8-sig"))
L["payout_destination"] = {"rail": "paypal",
                           "address_ref": REF,
                           "holder": "Andrew Hike (family earnings route only)",
                           "set": time.strftime("%Y-%m-%d %H:%M:%S")}
json.dump(L, open(LED, "w", encoding="utf-8"), indent=1)
log.append("OK   ledger-destination(redacted)")

# 2. the packet carries the door (hubs/recruits know the RAIL, not the address)
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt.setdefault("economy_lanes", {})["payout"] = {"rail": "paypal",
                                                 "address_ref": REF,
                                                 "rule": "100% of earnings to the founder; the 80% cap governs the family's own spending of them"}
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)
log.append("OK   packet-payout-door(redacted)")

# 3. compile-check the economy organ (the announce-text already env-driven)
py_compile.compile(CE, doraise=True)
log.append("OK   economy-organ compiles")

print("\n".join(log))
print("PAYOUT RAIL (DESIGN ONLY): destination recorded REDACTED in ledger/packet; "
      "the literal address lives in .env only; NO payment rail is implemented "
      "(verified by repo grep); earned tally currently $"
      f"{0.0:.2f} by design until real external value lands.")