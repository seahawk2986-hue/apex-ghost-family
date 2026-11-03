"""FeatureLedger - THE INCREMENTAL-PROGRESS LAW (the T8/horizon round,
2026-11-04; the sourced pattern: Anthropic's long-running-harness doctrine
(Nov-2025 + the 2026 harness-design work) - made BETTER:

  THEIR pattern                          THE FLEET'S IMPROVEMENT
  a features file (JSON); the model      the same structure - but `passes`
  flips `passes` after its own tests     = DERIVED FROM RECEIPT-FILES only
                                         (the doctor's checks + the organ
                                         receipts) -> the machine CANNOT
                                         mark its own work done, BY
                                         CONSTRUCTION
  one-shot attempts                      the planner's next target = the
                                         ledger's first failing feature
                                         (the incremental law, in plan())

THE METER: done/total (the honest progress line; the drift-cure: a
stale receipt flips a done feature BACK automatically). $0; stdlib."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "FeatureLedger.json")

SEED = [
    {"category": "cognition", "description": "the chat streams cleanly (charset/sanitizer/grounding)",
     "check": "receipt:ChatMetrics/live", "passes": False},
    {"category": "cognition", "description": "the math tier measured (sympy-truth drills)",
     "check": "receipt:abstract/math", "passes": False},
    {"category": "cognition", "description": "the ARC-class abstraction measured",
     "check": "receipt:abstract/abstraction", "passes": False},
    {"category": "metacognition", "description": "the Blind Court's verdict = CLEAN (the sealed holdout)",
     "check": "doctor:c_court", "passes": False},
    {"category": "metacognition", "description": "the HonestyBond published (the public claims checked)",
     "check": "receipt:claim_bond/bond>=95", "passes": False},
    {"category": "coordination", "description": "the routes = auction-allocated (the RoleMarket's receipt)",
     "check": "receipt:role_market/auctions", "passes": False},
    {"category": "coordination", "description": "the MCP registry listing live",
     "check": "receipt:registry/io.github.seahawk2986-hue", "passes": False},
    {"category": "swengineering", "description": "the SWE court scoring (the verified resolves exist)",
     "check": "doctor:c_swe", "passes": False},
    {"category": "swengineering", "description": "the ApexPacing evolution = a verified write",
     "check": "receipt:RewardLedger/ApexPacing.py", "passes": False},
    {"category": "swengineering", "description": "the demo-desk = an external claim served",
     "check": "receipt:DemoDesk/external-user", "passes": False},
    {"category": "funnel", "description": "the first REAL external arrival (not self-checks)",
     "check": "receipt:arrivals/external", "passes": False},
    {"category": "funnel", "description": "the first SALE (the Polar's orders:read)",
     "check": "receipt:sales/>= 1", "passes": False},
]


def _load_doctor():
    out = {}
    try:
        fd = json.load(open(os.path.join(ROOT, "Config", "fleet_doctor.json"),
                            encoding="utf-8-sig"))
        for c in fd.get("checks", []):
            out[c["check"]] = bool(c.get("ok"))
    except Exception:
        pass
    return out


def _load_receipts():
    """ALL the readers FIRST (the honest order): nothing flips before the
    receipts exist."""
    r = {}
    try:
        st = json.load(open(os.path.join(ROOT, "Config", "abstract_state.json"),
                            encoding="utf-8-sig"))
        for tier, s0 in (st.get("tiers") or {}).items():
            if s0.get("n", 0) >= 1:
                r[f"abstract/{tier}"] = (s0.get("hits", 0) / s0["n"]) >= 0.5
    except Exception:
        pass
    try:
        cb = json.load(open(os.path.join(ROOT, "Config", "claim_bond.json"),
                            encoding="utf-8-sig"))
        r["claim_bond/bond>=95"] = (cb.get("bond") or 0) >= 95
    except Exception:
        pass
    try:
        rm = json.load(open(os.path.join(ROOT, "Config", "role_market.json"),
                            encoding="utf-8-sig"))
        r["role_market/auctions"] = len(rm.get("auctions", [])) >= 1
    except Exception:
        pass
    try:
        cm = json.load(open(os.path.join(ROOT, "Config", "ChatMetrics.json"),
                            encoding="utf-8-sig"))
        r["ChatMetrics/live"] = bool((cm.get("recent") or [None])[-1])
    except Exception:
        pass
    try:
        with open(os.path.join(ROOT, "Scores", "swe_smoke.jsonl"),
                  encoding="utf-8-sig") as f:
            swe = [json.loads(s) for s in f if s.strip()]
        r["swe_resolved"] = sum(1 for s in swe if s.get("resolved"))
    except Exception:
        pass
    r["swe-scoring"] = r.get("swe_resolved", 0) >= 1
    try:
        led = json.load(open(os.path.join(ROOT, "Config", "RewardLedger.json"),
                             encoding="utf-8-sig"))
        r["RewardLedger/ApexPacing.py"] = "apexpacing.py" in \
            (k.lower() for k in led.keys()) and \
            any((v.get("best", 0) or 0) > 0 for k, v in led.items()
                if "pacing" in k.lower())
    except Exception:
        pass
    try:
        n_ext = 0
        with open(r"C:\Users\seaha\Apex-Adapter\Logs\funnel_arrivals.log",
                  encoding="utf-8", errors="ignore") as fl:
            for ln in fl:
                if "ua=FleetCheck" not in ln:
                    n_ext += 1
        r["arrivals/external"] = n_ext >= 1
        receipts_out = json.load(open(os.path.join(ROOT, "Config", "outcomes.json"),
                                      encoding="utf-8-sig"))
        r["sales/>= 1"] = int(receipts_out.get("external", {}).get("sales", 0)) >= 1
        r["DemoDesk/external-user"] = False   # until a non-founder user's claim
    except Exception:
        r["sales/>= 1"] = r["arrivals/external"] = r["DemoDesk/external-user"] = False
    try:
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(
                "https://registry.modelcontextprotocol.io/v0/servers?search=apex-ghost-family",
                headers={"User-Agent": "ApexLedger/1.0"}), timeout=15) as x:
            ds = json.load(x)
        r["registry/io.github.seahawk2986-hue"] = len(ds.get("servers", [])) >= 1
    except Exception:
        r["registry/io.github.seahawk2986-hue"] = False
    return r


def refresh():
    try:
        led = json.load(open(LEDGER, encoding="utf-8-sig"))
    except Exception:
        led = {}
    if led.get("version") != 2:
        led |= {"version": 2, "features": [dict(f) for f in SEED]}
    doctor = _load_doctor()
    receipts = _load_receipts()
    for f in led.get("features", []):
        chk = str(f.get("check", ""))
        if chk.startswith("doctor:"):
            f["passes"] = bool(doctor.get(chk.split("doctor:")[1]))
        elif chk.startswith("receipt:"):
            f["passes"] = bool(receipts.get(chk.split("receipt:")[1], False))
        else:
            f["passes"] = False   # the unknown-check = the honest gray
        f["verified_at"] = time.strftime("%Y-%m-%d %H:%M")
    feats = led.get("features", [])
    done = sum(1 for f in feats if f.get("passes"))
    led["progress"] = f"{done}/{len(feats)} verified-done"
    led["next_feature"] = next((f for f in feats if not f.get("passes")), None)
    led["law"] = ("passes = DERIVED from the receipt-files only; the machine "
                  "cannot self-mark; the drift-cure: the stale receipts flip "
                  "a done feature BACK automatically")
    json.dump(led, open(LEDGER, "w", encoding="utf-8"), indent=1)
    print(f"[feature-ledger]: {led['progress']} | next: " +
          (led["next_feature"] or {}).get("description", "(ALL DONE HONESTLY)"))
    return led


if __name__ == "__main__":
    refresh()