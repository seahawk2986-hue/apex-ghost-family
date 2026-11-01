"""THE FOUNDER-GATES CHECK: which of the 2 clicks are still open?
1. the demo-repo's existence (the public GitHub check)
2. the Polar store's products (the OAT-auth check)
3. the og-banner's live-serve (the last site-verify)"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("== gate 2b: the demo-repo ==")
try:
    with urllib.request.urlopen(
        "https://api.github.com/repos/seahawk2986-hue/open-triage-demo",
        timeout=20,
    ) as r:
        d = json.loads(r.read().decode())
        print(f"  EXISTS: {d.get('full_name')} (created {d.get('created_at')})")
        print("  -> DemoDesk's watch = unblocked on next beat")
except Exception as e:
    print(f"  NOT YET ({str(e)[:40]}) - item 2b = still founder's")

print("== gate 2: the Polar store ==")
env = {}
try:
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
except Exception as e:
    print(f"  the .env read honest: {str(e)[:60]}")
tok = env.get("POLAR_OAT", "")
org = env.get("POLAR_ORG_ID", "")
H = {"Authorization": f"Bearer {tok}", "User-Agent": "apex/1.0",
     "Accept": "application/json"}
if tok:
    try:
        with urllib.request.urlopen(urllib.request.Request(
            "https://api.polar.sh/v1/products?limit=10", headers=H),
            timeout=20) as r:
            d = json.loads(r.read().decode())
            items = d.get("items", d if isinstance(d, list) else [])
            print(f"  products reachable: {len(items)}")
            for p in items[:5]:
                print(f"    - {p.get('name')} (archived={p.get('is_archived')})")
    except Exception as e:
        print(f"  the products-read honest: {str(e)[:80]}")
    try:
        with urllib.request.urlopen(urllib.request.Request(
            f"https://api.polar.sh/v1/organizations/{org}", headers=H),
            timeout=20) as r:
            o = json.loads(r.read().decode())
            keys = ("slug", "status", "trial_ended_at", "is_under_review")
            print("  org:", {k: o.get(k) for k in keys if k in o})
    except Exception as e:
        print(f"  the org-read honest: {str(e)[:80]}")
else:
    print("  the OAT = not in .env (honest)")

print("== bonus: the og-banner live-serve ==")
try:
    with urllib.request.urlopen(
        "https://seahawk2986-hue.github.io/apex-ghost-family/og_banner.png",
        timeout=25,
    ) as r:
        b = r.read()
        print(f"  HTTP {r.status}, {len(b)} bytes - the og:image = LIVE")
except Exception as e:
    print(f"  the png-read honest: {str(e)[:60]} (CDN = may lag mins)")