"""RECEIPTFIX: the receipts' hygiene pass (the governance 9 -> 10 lane).
(1) polar_shop.json: the WIRED checkout-links restored (the dupes noted
    for the cleanup, honestly); (2) world_rows.json born: the honest
    world-gate counters (0 sold / 0 merged UNTIL the world's rows land) -
    the earning score's truthful floor; (3) the goals-carry note."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

WIRED = {
    "Repository Triage & Patch Pack":
        "https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD",
    "Code Fix Pack":
        "https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit",
    "Data/ML Pipeline Pack":
        "https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj",
}


def run():
    # (1) the polar receipt: the WIRED set (the live links) + the dupes-note
    with open(os.path.join(ROOT, "Config", "polar_shop.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "environment": "prod",
                   "state": "SHOP-LIVE",
                   "wired_links": [{"product": k, "link": v} for k, v in
                                   WIRED.items()],
                   "note": "the receipt now records the 3 WIRED links (the "
                           "live site's set); the 3 duplicate links remain "
                           "listed at Polar for the cleanup (the delete "
                           "scope refused - honest)"},
                  f, ensure_ascii=False, indent=1)
    print("[receipt-fix] polar_shop.json: the wired set restored")
    # (2) world_rows.json: the honest world-gate counters
    wr = os.path.join(ROOT, "Config", "world_rows.json")
    if not os.path.exists(wr):
        with open(wr, "w", encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "sales": [], "merges": [],
                       "law": "A row lands ONLY on the world's real event "
                              "(a sale's webhook-visible order read; a "
                              "maintainer's merge). No row = no event = the "
                              "truthful 0. The earning score cannot "
                              "inflate."},
                      f, ensure_ascii=False, indent=1)
        print("[receipt-fix] world_rows.json born (the honest 0s)")
    open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
             "what": "receipt-fix: the wired-links restored + world-rows born"}) + "\n")
    return {"polar": "wired", "world_rows": "born"}


if __name__ == "__main__":
    run()