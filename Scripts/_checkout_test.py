import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PolarAgent as PA

tok = PA.org_token()[0]
BASE = "https://api.polar.sh"
# 1. the products' ids (the live!)
st, prods = PA.api("/v1/products/?limit=20", tok, base=BASE)
prods = prods.get("items") if st == 200 else []
triage = next((p for p in prods if "Triage" in p.get("name", "")), None)
if not triage:
    print("the products' state:", st, len(prods))
    sys.exit(1)
pid = triage.get("id")
print("the Triage-pack's live id:", pid[:12], "| price:",
      [pr.get("price_amount", 0) / 100 for pr in triage.get("prices", [])])
# 2. the REAL checkout-session (the $0 verification of the buy-flow!)
st2, chk = PA.api("/v1/checkouts/", tok, method="POST", payload={
    "products": [pid], "allow_discount_codes": True}, base=BASE)
if st2 in (200, 201):
    print("THE CHECKOUT SESSION IS LIVE:", chk.get("url") or "?")
    print("  the checkout's id:", chk.get("id", "?")[:20])
    print("  the price shown:", chk.get("total_amount", 0) / 100)
else:
    print("the checkout-session:", st2, json.dumps(chk)[:200])
# 3. the orders'/payout state (the scopes' truth)
st3, orders = PA.api("/v1/orders/?limit=5", tok, base=BASE)
print("the orders' read:", st3, "->", "the scopes OK" if st3 == 200 else
      json.dumps(orders)[:120])