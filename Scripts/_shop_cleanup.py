import json
import os
import sys
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PolarAgent as PA

tok = PA.org_token()[0]
BASE = "https://api.polar.sh"
st, links = PA.api("/v1/checkout-links/?limit=50", tok, base=BASE)
print("the links' HTTP:", st)
items = links.get("items", []) if st == 200 else []
print("TOTAL checkout links on the account:", len(items))
keep = set()
try:
    shop = json.load(open(os.path.join(ROOT, "Config", "polar_shop.json"),
                          encoding="utf-8-sig"))
    keep = {l0["link"] for l0 in shop.get("checkout_links", [])}
except Exception:
    pass
card = json.load(open(os.path.join(ROOT, "family", "agent_card.json"),
                      encoding="utf-8-sig"))
for b in card.get("buy", []):
    keep.add(b.get("checkout", ""))
print("\nOUR WIRING points at:")
for k0 in sorted(keep):
    print("  ", k0)
print("\nthe full inventory:")
for l0 in items:
    print("  -", l0.get("id", "?")[:26], "|", l0.get("label", "?")[:34],
          "| url:", l0.get("url", "?")[:70])

# delete the NEWER duplicates (the ones NOT in our wiring set)
removed = 0
for l0 in items:
    if l0.get("url") in keep:
        print("  KEEP:", l0.get("label", "?")[:30])
        continue
    d = PA.api(f"/v1/checkout-links/{l0['id']}", tok, method="DELETE",
               base=BASE)
    removed += (d[0] in (200, 204, 404))
print(f"\nremoved {removed} duplicate link(s) — the wired originals stand")
# the products' final honest list (the read)
st3, prods = PA.api("/v1/products/?limit=50", tok, base=BASE)
print("\nTHE PRODUCTS", f"(http {st3}):")
for p in (prods.get("items") or []):
    prices = [pr.get("price_amount", 0) / 100 for pr in p.get("prices", [])]
    print(f"  - {p.get('name')} (${prices}) | {p.get('visibility')}")