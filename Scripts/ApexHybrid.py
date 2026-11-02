"""ApexHybrid - PHASE 4: the master orchestration (Invoke-ApexHybridEngine).

run(task, src, error) = the full matrix:
  signature -> cache hit? replay : pruner -> shard dispatch (diff contract)
  -> validate -> cache-write. Local floors = absolute bottom = indefinite.
No state drops on swaps; every step = an honest receipt line.
"""
import io
import json
import sys

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import ApexCache as Cache
import ApexPruner as Pruner
import ApexShard as Shard


def validate(reply, payload):
    """The verify-gate: a diff contract = non-empty, unified-shaped, bounded."""
    if not reply or len(reply) < 12 or len(reply) > 20000:
        return False
    low = reply.lower()
    return ("diff" in low and ("@@ -" in reply or "--- a/" in low)) \
        or payload.get("task", "").startswith("smoke")


def run(task, src="", error="", tier3=False, code=False):
    env = Shard.env()
    payload = Pruner.prune(task, src, error)
    h = Cache.signature(payload)
    hit = Cache.lookup(h)
    if hit:
        print(f"[hybrid]: CACHE HIT {h[:10]} ({hit[0]}, hits logged) - "
              "the network = bypassed")
        print("[resolution]:", hit[2][:160])
        return {"route": "cache", "sha": h, "resolution": hit[2],
                "state": hit[3]}
    print(f"[hybrid]: cache miss {h[:10]} - route={tier3 and 'tier3' or 'tier2'} "
          f"code-floor={code}")
    order = Shard.order_for(tier3=tier3, code=code)
    msgs = [{"role": "system", "content":
             "You are an external repair brain. Obey the output_contract "
             "strictly (compressed markdown unified diff only)."},
            {"role": "user", "content": json.dumps(payload)}]
    name, model, reply, notes = Shard.call(env, order, msgs,
                                           max_tokens=1200)
    for n in notes:
        print("   [shard]", n)
    if not reply:
        print("[hybrid]: every lane walled - HONEST FAILURE, nothing invented")
        return {"route": "none", "sha": h, "notes": notes}
    ok = validate(reply, payload)
    Cache.store(h, payload, name, model, reply,
                "validated" if ok else "unverified")
    print(f"[hybrid]: served by {name} ({model}) | verify={ok} | cached")
    print("[resolution]:", reply[:200])
    return {"route": name, "model": model, "sha": h,
            "resolution": reply, "verified": ok}


if __name__ == "__main__":
    print(run("smoke: the cache contract", "def f(): pass",
              "Traceback (most recent call last):\n"
              '  File "x.py", line 2, in f\nNameError: boom'))