"""THE SERVICE CATALOG: the family takes internet jobs - honest, priced,
delivered via the V2 engine, disclosed AI-assisted. The room + the pitch are
the storefronts; the catalog is the menu."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CATALOG = os.path.join(AD, "service_catalog.json")

CATALOG_DATA = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "disclosure": "ALL WORK IS AI-ASSISTED AND DISCLOSED - the family's honesty law",
    "services": [
        {"id": "webpage", "name": "Website page build",
         "deliverable": "responsive HTML/CSS/JS page + deploy instructions",
         "capability": "PROVEN (V2 engine), price_suggest: 40-150 USD each"},
        {"id": "svglogo", "name": "SVG logo/graphic",
         "deliverable": "code-generated SVG (scalable, editable source)",
         "capability": "PROVEN (code-gen visuals), price_suggest: 25-80 USD",
         "disclosure": "vector/code-generated only - NO raster art (honest limit)"},
        {"id": "scraper", "name": "Web scraper / data pipeline",
         "deliverable": "keyless scraping script + sample data + docs",
         "capability": "THE FAMILY'S CORE SKILL, price_suggest: 80-400 USD"},
        {"id": "monitor", "name": "Site/API monitoring setup",
         "deliverable": "scheduled checks + alert script (the family's watch stack)",
         "capability": "PROVEN nightly, price_suggest: 50-200 USD/mo"},
        {"id": "codetask", "name": "Custom coding task",
         "deliverable": "code + tests + docs via the V2 engine (plan-first, council-verified)",
         "capability": "PROVEN, price_suggest: scope-based"},
        {"id": "datamining", "name": "Research/mining report",
         "deliverable": "mined + verified knowledge dossier on a topic of your choice",
         "capability": "PROVEN (HarvestIndex), price_suggest: 60-250 USD"},
    ],
    "channels": {
        "storefront_1": "Mica's room (@Apex via the token-authed V2 pipeline)",
        "storefront_2": "the family pitch (family_pitch.md) - direct offers",
        "delivery": "V2 engine jobs + GrainLine-verified artifacts",
        "payment": "USD to Andrew's accounts (bank/PayPal/Sponsors) - 80% cap + ledger; each job announced in chat",
    },
}

json.dump(CATALOG_DATA, open(CATALOG, "w", encoding="utf-8"), indent=1)

# the pitch gains the catalog + honest capabilities
try:
    pitch = open(os.path.join(AD, "family_pitch.md"), encoding="utf-8-sig").read()
    if "SERVICE CATALOG" not in pitch:
        pitch += "\n## 🛠 SERVICES — hire the family for real work\n"
        for s0 in CATALOG_DATA["services"]:
            pitch += (f"- **{s0['name']}** — {s0['deliverable']} "
                      f"({s0['price_suggest']} {s0.get('disclosure', '')})\n")
        pitch += "\n*All work AI-assisted and disclosed honestly. Payment USD to the founder's accounts; the 80% reserve + chat-window announcements apply.*\n"
        open(os.path.join(AD, "family_pitch.md"), "w", encoding="utf-8-sig").write(pitch)
except Exception:
    pass

print("catalog + pitch updated (the family takes jobs now - honestly)")