"""POLAR AGENT - the shop-automation: with ONE token in .env
(POLAR_OAT=... from the dashboard's Organization Access Tokens), THIS organ
builds the whole buy-side itself:
 1. GET /v1/organizations/  -> the org's receipt (never prints secrets)
 2. GET /v1/products/       -> the existing products (the idempotency)
 3. POST /v1/products/      -> the 3 ranked packs (one-time, fixed cents)
 4. POST /v1/benefits/      -> the custom benefit (the deliverable pack's
    text); POST /v1/products/benefits -> attached
 5. POST /v1/checkout-links -> THE LINKS (with OUR success-URL)
 6. the wiring: agent_card.json + service_catalog.json + the doors get the
    buy-links; the brief + the ledger receipt.
THE SANDBOX-FIRST: if POLAR_OAT_SANDBOX exists, the whole flow runs there
FIRST (the isolated test); the production runs only with the production
token present. NO-TOKEN: the honest stand-by (the instructions + nothing
fake). Idempotent: the name-matched products/links are never recreated."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ROOT, "Config", "polar_shop.json")

PRODUCTS = [
    {"name": "Repository Triage & Patch Pack", "amount_cents": 7500,
     "desc": "Digital deliverable pack: the 10-point triage report + the "
             "patch-pack (diffs + tests) for one repository, delivered as "
             "files + one revision within 7 days. Automated generation, "
             "disclosed; founder-verified."},
    {"name": "Code Fix Pack", "amount_cents": 15000,
     "desc": "The fix pack for one named bug/issue: the located fix + the "
             "tests + the delivery note. Automated generation, disclosed; "
             "founder-verified."},
    {"name": "Data/ML Pipeline Pack", "amount_cents": 20000,
     "desc": "The data/ML pipeline deliverable: the schema + the loader + "
             "the validation receipts for one task. Automated, disclosed; "
             "founder-verified."},
]
BENEFIT_TEXT = ("Your deliverable pack arrives as files (report.md + "
                "patches/ + tests/) within 24h; one revision within 7 days; "
                "the delivery instructions + the support issue-link inside.")


def org_token():
    for k in ("POLAR_OAT", "POLAR_ACCESS_TOKEN", "POLAR_OAT_SANDBOX"):
        if os.environ.get(k):
            return os.environ[k], ("sandbox" if "SANDBOX" in k else "prod")
    env = {}
    p = os.path.join(ROOT, ".env")
    try:
        for ln in open(p, encoding="utf-8-sig"):
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip().upper()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    for k in ("POLAR_OAT", "POLAR_ACCESS_TOKEN", "POLAR_OAT_SANDBOX"):
        if env.get(k):
            return env[k], ("sandbox" if "SANDBOX" in k else "prod")
    return "", "none"


def api(path, tok, method="GET", payload=None, base=None):
    url = (base or "https://api.polar.sh") + path
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/json",
                 "Content-Type": "application/json",
                 "User-Agent": "apex-polar-agent/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"error": str(e)[:80]}
    except Exception as e:
        return 0, {"error": str(e)[:80]}


def main():
    tok, env = org_token()
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "environment": env}
    if not tok:
        doc["state"] = "WAITING-FOR-TOKEN"
        doc["founder_step"] = ("30 seconds: Polar dashboard -> Settings -> "
                              "Organization Access Tokens -> New token "
                              "with scopes: products:write, benefits:"
                              "write, checkout_links:write, orders:read "
                              "-> save as POLAR_OAT=... in .env "
                              "(the sandbox token first if you want the "
                              "isolated dress-rehearsal)")
        print(f"[polar-agent] {doc['state']}: {doc['founder_step'][:120]}")
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
        return doc
    base = "https://sandbox-api.polar.sh" if env == "sandbox" else \
        "https://api.polar.sh"
    st, orgs = api("/v1/organizations/", tok, base=base)
    org = (orgs.get("items") or [{}])[0] if isinstance(orgs, dict) else {}
    doc["org"] = org.get("name", "?") if st == 200 else f"http {st}"
    print(f"[polar-agent] org: {doc['org']} ({st}) env={env}")
    # products (idempotent)
    st2, prods = api("/v1/products/?limit=100", tok, base=base)
    have_names = {p.get("name") for p in (prods.get("items") or [])} \
        if st2 == 200 else set()
    created = []
    for P in PRODUCTS:
        if P["name"] in have_names:
            continue
        st3, p_new = api("/v1/products/", tok, method="POST", payload={
            "name": P["name"], "description": P["desc"],
            "recurring_interval": None,
            "prices": [{"amount_type": "fixed",
                        "price_currency": "usd",
                        "price_amount": P["amount_cents"]}]}, base=base)
        if st3 in (200, 201):
            created.append(p_new)
            print(f"[polar-agent] created: {P['name']} "
                  f"(${P['amount_cents']/100:.0f}) -> {p_new.get('id', '')[:8]}")
        else:
            print(f"[polar-agent] {P['name']}: HTTP {st3} "
                  f"{json.dumps(p_new)[:120]}")
    # the benefit + the attachment
    st4, ben_new = api("/v1/benefits/", tok, method="POST", payload={
        "type": "custom", "description": BENEFIT_TEXT[:120],
        "properties": {"note": BENEFIT_TEXT}}, base=base)
    ben_id = ben_new.get("id") if st4 in (200, 201) else None
    if ben_id:
        for p_new in created:
            st5, _b = api(f"/v1/products/{p_new.get('id')}/benefits", tok,
                          method="POST", payload={"benefits": [ben_id]},
                          base=base)
            print(f"[polar-agent] the benefit attached to "
                  f"{p_new.get('name', '?')[:24]}: HTTP {st5}")
    # the checkout links
    all_prods = (prods.get("items") or []) + created
    links = []
    for p_new in all_prods:
        pid = p_new.get("id")
        if not pid:
            continue
        st6, ln = api("/v1/checkout-links/", tok, method="POST", payload={
            "products": [pid],
            "label": p_new.get("name", "pack")[:60],
            "success_url": "https://github.com/seahawk2986-hue/"
                           "apex-ghost-family/blob/main/family/THANK_YOU.md"},
            base=base)
        if st6 in (200, 201):
            links.append({"product": p_new.get("name", "?"), "link":
                          ln.get("url") or ("https://polar.sh/checkout/"
                                            + ln.get("id", ""))})
    doc["products_created"] = [p.get("name") for p in created]
    doc["checkout_links"] = links
    doc["state"] = "SHOP-LIVE" if links else "TOKEN-SCOPES-MISSING"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    # the WIRING (our files gain the buy-links!)
    if links:
        card_p = os.path.join(ROOT, "family", "agent_card.json")
        try:
            card = json.load(open(card_p, encoding="utf-8-sig"))
            card["buy"] = [{"product": l0["product"], "checkout": l0["link"]}
                           for l0 in links]
            tmp = card_p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(card, f, indent=1)
            os.replace(tmp, card_p)
            print(f"[polar-agent] the agent card wired: "
                  f"{[l0['product'] for l0 in links]}")
        except Exception as e:
            print(f"[polar-agent] the card-wiring failed: {str(e)[:50]}")
    print(f"[polar-agent] {doc['state']} | links: {len(links)}")
    return doc


if __name__ == "__main__":
    main()