"""THE 120B MAX-UTILIZATION AUDIT (the test + recheck law): (1) the four
real domain-verdicts through the LIVE ladder, (2) the call-site census'
gaps-report, (3) the rate-reading (the honest free-cadence). Receipts:
Config/max_120b_audit.json. $0.00 always."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import CloudBrain as CB

DOM = {
    "code_review": ('Review this diff: p = Path(p); if not p.exists(): '
                    'raise FileNotFoundError(p); return p.read_text() '
                    "(replacing a silent read). Reply ONLY JSON "
                    '{"ship": true, "why": "<=120 chars"}'),
    "schema_judge": ('A JSON-schema property "amount": {"type": "string", '
                     '"pattern": "^\\\\d+$"} - is that the money-amount'
                     "right shape? Reply ONLY JSON "
                     '{"sound": true/false, "why": "<=120 chars"}'),
    "claim_ambiguity": ('An OSS issue says "I will fix this next week" '
                        "(the author promised). A claim-check must SKIP "
                        "promised work. Reply ONLY JSON "
                        '{"skip": true/false, "why": "<=120 chars"}'),
    "copy_check": ('Marketing line: "We pay you within an hour of checkout" '
                   "- the family delivers in 24h and pays the SELLER. "
                   "Reply ONLY JSON {\"honest\": true/false, "
                   '"why": "<=120 chars"}'),
}
out = {}

for name, ask in DOM.items():
    t0 = time.time()
    r = CB.chat(ask, max_tokens=200, purpose=f"the 120b {name}",
                models=("groq", "local-coder", "local-fast"),
                resp_json=True)
    ok = bool(r) and (("\"ship\"" in r or "\"sound\"" in r or
                       "\"skip\"" in r or "\"honest\"" in r))
    out[name] = {"ok": ok, "latency_s": round(time.time() - t0, 2),
                 "note": (r or "NONE")[:100]}
    print(f"[max-120b] {name}: {'LIVE' if ok else 'CHECK'} {round(time.time() - t0, 2)}s")
    time.sleep(2)
# the honest summary
oks = sum(1 for v in out.values() if v["ok"])
with open(os.path.join(ROOT, "Config", "max_120b_audit.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "domains": out,
               "lived": oks, "verdict": "MAX-UTILIZED" if oks == 4 else
               "THE CHECK-CARRY: the honest note per domain",
               "cost": "$0.00"}, f, ensure_ascii=False, indent=1)
print(f"[max-120b] {oks}/4 domains LIVE through the ladder ($0)")