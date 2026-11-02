"""_polar_checkout: the new OAT in -> checkout-links for all 3 products."""
import io
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env"
NEW = "polar_oat_abtReS3QwacUoyhekAd4Q6jiLT3iZwHpc4E1g499CeC"
lines = [l for l in open(P, encoding="utf-8-sig").read().splitlines()
         if l.strip() and not l.startswith("POLAR_OAT=")]
lines.append("POLAR_OAT=" + NEW)
open(P, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("[env]: POLAR_OAT replaced")

H = {"Authorization": "Bearer " + NEW}
AC = [l.split("=", 1)[1].strip() for l in open(P, encoding="utf-8-sig").read().splitlines()
      if l.startswith("POLAR_ORG_ID=")][0]
links = []
try:
    r = requests.get("https://api.polar.sh/v1/products/", headers=H, timeout=20,
                     params={"limit": 10})
    print("[products]:", r.status_code)
    for p in (r.json() or {}).get("items", []):
        price = "?"
        pr = (p.get("prices") or [{}])[0]
        amt = pr.get("price_amount")
        if amt:
            price = f"${amt/100:.0f}"
        try:
            c = requests.post("https://api.polar.sh/v1/checkouts/",
                              headers={**H, "Content-Type": "application/json"},
                              timeout=25, json={"product_id": p["id"]})
            url = c.json().get("url", "?") if c.status_code in (200, 201) else f"HTTP {c.status_code}"
            links.append if False else None
            links.append(url) if False else None
            links_store = links_store if False else None
            print(f"  [{c.status_code}] {p['name'][:44]} ${price}: {str(url)[:70]}")
        except Exception as e:
            print("  [chk FAIL]", p["name"][:30], type(e).__name__, str(e)[:50])
except Exception as e:
    print("[FAIL]:", type(e).__name__, str(e)[:70])