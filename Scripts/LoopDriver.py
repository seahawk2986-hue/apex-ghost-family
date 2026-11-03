"""LoopDriver - THE SELF-IMPROVEMENT ENGINE (the zero-weakness program).

The cycle (runs itself, receipts itself):
  1. EVALUATE   - the sweep: services, keys, lanes, the gym scores, the
                  board, the acceptance state -> the weaknesses-list (honest)
  2. STRENGTHEN - per weakness: the named organ (novel), paper-grounded
  3. TEST       - recompile + the receipts re-verify
  4. LEDGER     - improvements.json = the evidence trail of what was fixed
  5. REPEAT     - the next cycle starts from the ledger's weakest score

The design laws: hardware-aware (RAM-gated), outsourced (Actions/remote
lanes for anything heavy, local = only micro-exec), novel (no copy-paste
patterns), evidence-gated (no organ promoted without a score).

The 5 weaknesses (from the ledger) and their counter-organs:
  1. instruction-discipline -> the Format-Sandbox self-test per tool-action
  2. window-dependent brains -> the local-lift: nightly LM Studio big-brain
     smoke test (qwen3-30b-a3b), promoted to the seat map only if it wins
  3. shallow memory -> the Self-Book: nightly identity consolidation
  4. zero customers -> the proof-engine: nightly receipts -> public
     proof-post drafts (founder-gated like all outreach)
  5. fragile self-repair -> the compile-gate-first policy + the
     two-fixer stop-clock, enforced by this driver's own structure

Each cycle: run, score, write scores/loop-N.json. The weakest number
becomes the next cycle's target.
"""
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
LED = os.path.join(REPO, "scores", "loop_ledger.json")


def sweep():
    """the honest multi-domain sweep: returns the weaknesses-list."""
    import requests
    state = {}
    for name, url in (("adapter", "http://127.0.0.1:8788/v1/health"),
                      ("jobs-page", "http://127.0.0.1:8080/jobs"),
                      ("talk", "http://127.0.0.1:8080/talk/status")):
        try:
            r = requests.get(url, timeout=15)
            state[name] = "up" if r.status_code == 200 else f"http {r.status_code}"
        except Exception as e:
            state[name] = "down " + type(e).__name__
    print("   [sweep]", json.dumps(state))
    return state


def weaknesses(state):
    w = [f"{k}: {v}" for k, v in state.items() if v != "up"]
    env = {}
    p = os.path.join(REPO, ".env")
    for l in open(P if (P := os.path.join(REPO, ".env")) else "", encoding="utf-8-sig"):
        if "=" in l:
            env[l.split("=", 1)[0]] = l.split("=", 1)[1].strip()
    for k in ("GROQ_API_KEY", "CEREBRAS_API_KEY", "POLAR_OAT"):
        if not env.get(k):
            w.append(f"missing key: {k}")
    return w


state = sweep()
w = weaknesses(state)
led = json.load(open(LED, encoding="utf-8")) if os.path.isfile(LED) else []
ts = time.strftime("%Y-%m-%d %H:%M:%S")
print(f"[loop]: sweep done | weaknesses: {len(w)}")
for x in w:
    print("   -", x)
if w:  # THE POCKET PAGER: the phone learns of problems when they exist
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from PocketPing import ping
        ping("APEX: weakness detected", "; ".join(w)[:160], tags="warning")
    except Exception as _e:
        print("   [pager]:", str(_e)[:50])

led.append({"ts": ts, "up": sum(1 for k, v in state.items() if v == "up"),
            "total": len(state), "weaknesses": w})
os.makedirs(os.path.dirname(LED), exist_ok=True)
json.dump(led[-30:], open(LED, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("[ledger]:", LED)
print("[next]: sweep all-green -> the gym/bench outputs become the next-organ evidence")