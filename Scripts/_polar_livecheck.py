"""THE POLAR LIVE-MODE CHECK ($0, no charge): create a checkout session
for the cheapest product and read which domain it lands on.
  polar.sh/...       = LIVE (the go-live = already done, nothing to click)
  sandbox.polar.sh/  = TEST (the go-live toggle = still needed)"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
    ln = ln.strip()
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()
H = {"Authorization": f"Bearer {env.get('POLAR_OAT','')}",
     "Content-Type": "application/json", "User-Agent": "apex/1.0"}

with urllib.request.urlopen(urllib.request.Request(
    "https://api.polar.sh/v1/products?limit=10", headers=H), timeout=25) as r:
    prods = json.loads(r.read().decode()).get("items", [])
cheapest = None
for p in prods:
    for price in p.get("prices", []):
        amt = (price.get("price_amount") or 0)
        if cheapest is None or amt < cheapest[0]:
            cheapest = (amt, p["id"], p.get("name"))
            pp = price.get("id")
print(f"the cheapest product: {cheapest[2] if cheapest else '?'} "
      f"({(cheapest[0] or 0) / 100:.0f} USD)" if cheapest else "no products")

if cheapest:
    body = json.dumps({"product_price_id": pp,
                       "success_url": "https://seahawk2986-hue.github.io/"
                                      "apex-ghost-family/"}).encode()
    try:
        url = None
        tgt = "https://api.polar.sh/v1/checkouts"
        for hop in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(
                    tgt, data=body, headers=H, method="POST"),
                    timeout=25) as r:
                    c = json.loads(r.read().decode())
                url = c.get("url", "?")
                break
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 307, 308):
                    tgt = e.headers.get("Location") or tgt
                    continue
                raise
    except Exception as e:
        print(f"the checkout-create honest: {str(e)[:80]}")
        url = None
    if url:
        mode = "SANDBOX = TEST-MODE (go-live still needed)" \
            if "sandbox" in url else "LIVE = the store accepts real sales NOW"
        print(f"checkout-url: {url[:80]}")
        print(f"VERDICT: {mode}")