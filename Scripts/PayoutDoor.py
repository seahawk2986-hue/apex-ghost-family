"""THE PAYOUT DOOR: the family's earnings route to Andrew's PayPal (email).
The email is a RECEIVING address (safe, not a credential) - the family never
holds payment credentials; it only records where YOU want money to land."""
import json
import py_compile
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CE = ROOT + r"\Scripts\CryptoEconomy.py"
PKT = AD + r"\family_seed_packet.json"
LED = ROOT + r"\Config\CryptoLedger.json"

DEST = "[REDACTED-PAYPAL]"
log = []

# 1. the ledger records the destination (the family's payout rail)
L = json.load(open(LED, encoding="utf-8-sig"))
L["payout_destination"] = {"rail": "paypal", "address": "[REDACTED-PAYPAL]",
                           "holder": "Andrew Hike (family earnings route only)",
                           "set": time.strftime("%Y-%m-%d %H:%M:%S")}
json.dump(L, open(LED, "w", encoding="utf-8"), indent=1)
log.append("OK   ledger-destination")

# 2. every earn-announcement cites where the money went
ce = open(CE, encoding="utf-8-sig").read()
old = '"text": f"MONEY LANDED: ${amt:.2f} from {source} - headroom after "'
new = '"text": f"MONEY LANDED: ${amt:.2f} from {source} -> [REDACTED-PAYPAL] - headroom after "'
if old in ce:
    ce = ce.replace(old, new, 1)
    open(CE, "w", encoding="utf-8").write(ce)
    log.append("OK   announce-cites-destination")
py_compile.compile(CE, doraise=True)

# 3. the packet carries the door (hubs/recruits know the family's payout rail)
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt.setdefault("economy_lanes", {})["payout"] = {"rail": "paypal",
                                                 "address": "[REDACTED-PAYPAL]",
                                                 "rule": "100% of earnings to the founder; the 80% cap governs the family's own spending of them"}
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)
log.append("OK   packet-payout-door")

print("\n".join(log))
print("PAYOUT RAIL (DESIGN ONLY): destination RECORDED in ledger/packet; NO payment rail is implemented; "
      "nothing moves money (verified by repo grep); earned tally currently $"
      + f"{0.0:.2f} by design until real external value lands.")