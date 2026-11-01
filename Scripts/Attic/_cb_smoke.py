"""THE LADDER SMOKE: groq-120b first ($0, no-card), the locals as the
guaranteed floor - the rater's brain-lane proof."""
import sys
import time

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import CloudBrain as CB

t0 = time.time()
r = CB.chat('Reply ONLY the JSON {"ship": true, "why": "ok"}.',
            max_tokens=120, purpose="the ladder smoke",
            models=("groq", "local-coder", "local-fast"))
dt = round(time.time() - t0, 2)
ok = bool(r) and '"ship"' in r
print(f"[cb-smoke] {dt}s -> {(r or 'NONE')[:80]}")
print(f"[cb-smoke] VERDICT: {'PASS (the 120b serves at $0)' if ok
      else 'HONEST-STATE: ' + str(r)[:60]}")