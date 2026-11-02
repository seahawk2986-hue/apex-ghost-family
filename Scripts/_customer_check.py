"""The customer-honesty check: real checkout states + real outreach sends."""
import io
import json
import os
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = {}
for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
    if "=" in ln:
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()

H = {"Authorization": "Bearer " + env.get("POLAR_OAT", ""),
     "Content-Type": "application/json"}
ORG = env.get("POLAR_ORG_ID", "")

try:
    r = requests.get("https://api.polar.sh/v1/checkouts",
                     params={"organization_id": ORG, "limit": 20},
                     headers=H, timeout=45)
    body = r.json()
    items = body.get("items", []) if isinstance(body, dict) else body.get("items", [])
    print("[checkouts queried]:", r.status_code, "| count:", len(items))
    states = {}
    for c in items:
        st = c.get("status", "?")
        states[st] = states.get(st, 0) + 1
        print("   ", (c.get("id") or "")[:10], "| state:", st,
              "| product:", str(c.get("product_id"))[:8],
              "| amount:", c.get("amount"))
    print("[state summary]:", states)
except Exception as e:
    print("[checkouts]:", type(e).__name__, str(e)[:100])

try:
    r2 = requests.get("https://api.polar.sh/v1/orders",
                      params={"organization_id": ORG, "limit": 10},
                      headers=H, timeout=45)
    orders = r2.json().get("items", [])
    print("[orders]:", len(orders), "(paid customers = orders)")
    for o in orders[:5]:
        print("   ", (o.get("id") or "")[:10], "|", o.get("status"),
              "|", o.get("amount"))
except Exception as e:
    print("[orders]:", type(e).__name__, str(e)[:100])

q = os.path.join(REPO, "outreach_queue.jsonl")
if os.path.isfile(q):
    rows = [json.loads(x) for x in open(q, encoding="utf-8") if x.strip()]
    sent = sum(1 for r3 in rows if r3.get("credentials_sent", 0))
    print(f"[outreach queue]: {len(rows)} rows | sent: {sent} (founder-gated, by design)")