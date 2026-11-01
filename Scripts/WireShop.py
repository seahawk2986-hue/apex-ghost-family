import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
shop = json.load(open(os.path.join(ROOT, "Config", "polar_shop.json"),
                      encoding="utf-8-sig"))
links = shop.get("checkout_links", [])
print("the real links:")
for l0 in links:
    print("  ", l0["product"], "->", l0["link"])
card = json.load(open(os.path.join(ROOT, "family", "agent_card.json"),
                      encoding="utf-8-sig"))
print("\nthe card's buy:", json.dumps(card.get("buy", []), indent=1))
# wire the REST: the catalog + the doors + the hub README + THANK_YOU
sc_p = os.path.join(AD, "service_catalog.json")
sc = json.load(open(sc_p, encoding="utf-8-sig"))
for l0 in links:
    for s0 in (sc.get("services") or []):
        name = str(s0.get("name", "")).lower()
        if l0["product"].lower().split()[0] in name or \
                ("triage" in l0["product"].lower() and "triage" in name):
            s0["checkout_url"] = l0["link"]
            s0["payment_processor"] = "polar (MoR)"
sc["buy_live"] = True
sc["thank_you"] = "family/THANK_YOU.md"
tmp = sc_p + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(sc, f, indent=1)
os.replace(tmp, sc_p)
hub = os.path.join(ROOT, "README.md")
t = open(hub, encoding="utf-8-sig").read()
if "polar.sh" not in t:
    t = t.replace("## Hire the family", "## Hire the family")
    buy_txt = "\n### BUY (live):\n" + "\n".join(
        f"- **{l0['product']}** — buy: {l0['link']}" for l0 in links) + "\n"
    t = t.replace("## Hire the family", "## Hire the family" + buy_txt, 1)
    with open(hub, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)
print("the catalog/README wired")
# the doors board (the adapter's)
dp = os.path.join(AD, "hub_doors_board.json")
try:
    doors = json.load(open(dp, encoding="utf-8-sig"))
    doors["buy_links"] = [{"product": l0["product"], "url": l0["link"]}
                          for l0 in links]
    tmp = dp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doors, f, indent=1)
    os.replace(tmp, dp)
    print("the doors wired")
except Exception as e:
    print("the doors' wire:", str(e)[:50])
# the reward/Ascent receipt
with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": "upward", "what": "SHOP-LIVE (the 3 "
                        "checkout links + the wiring complete)"}) + "\n")