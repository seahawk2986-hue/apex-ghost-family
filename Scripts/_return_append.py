"""APPEND the real-model-acceptance section to RETURN-TO-MICA.txt."""
ADD = """
== REAL-MODEL ACCEPTANCE ATTEMPT (Andrew-consented, 2026-11-01) - NOT PASSED ==
Consent path: local qwen2.5-coder-7b first (your pinned local-only design);
after its honest format-fail Andrew re-consented ONE Groq gpt-oss-120b
attempt (test-scope source-flip, hash-receipted, REVERTED after).
Bounds held: <=1000 tokens/request, no fallback, $0.00, image
apex-sandbox:latest (37dc381...), walls 120s/120s/60s, one workspace flow.

ATTEMPTS 1+2 (LOCAL, the deployed engine, ZERO source changes):
- Both jobs: warm model, 4-10x 'model reply was not a strict tool action'
  -> 'model-call budget exhausted (10/10)' -> honest job-failed.
- qwen2.5-coder-7b-instruct = reachable but cannot hold this engine's
  strict tool-action discipline.

ATTEMPT 3 (GROQ 120b; flip sha 14fd9164ad692928...; reverted after):
- The lane = LIVE: the model produced a REAL PLAN (write sleeper.py -> run
  -> monitor 5 ticks) and in J1 emitted strictly-PAIRED tool-actions
  (tool.started/finished with call_ids; the pairing discipline = ok).
- J1 RED: the model called finish BEFORE any write; the verify-COUNCIL
  honestly withheld it ('workspace was empty, no files listed') twice ->
  'second council mismatch - honest failure' -> job recorded failed.
- J3 cancel-drill: plan + 5 strict-format misses -> wall-clock budget out
  -> honest failure.
- VERDICT: NOT ACCEPTED across 3 tracked attempts. Nothing claimed.

== ENGINE FINDINGS (owner-side, for your repair queue) ==
1. SLOT-LEAK on the exception path: an engine-error job (NameError during a
   provider branch) leaves REG.data['_slot'] PERSISTED in
   jobs_registry.json; later POSTs = 409 'Busy: a coding job is active
   (slot held by <dead-rid>'; DELETE returns 200/failed/
   processes_stopped:true but CANNOT free a slot owned by a live lingering
   worker-thread; a RESTART does not clear it either (a failed record sits
   outside the queued/running/cancelling reconcile-net). Owner cleared it
   by registry surgery (adapter stopped; _slot popped; atomic flush;
   restart; healthy). The honest-fail path releases the slot CORRECTLY -
   only the exception path leaks.
2. RETRY-NUDGE without a format-spec: 'model reply was not a strict tool
   action; asking again' carries no shape/example - strict compliance
   stayed intermittent even for the tool-native 120b.
3. The verify-council = EXCELLENT (it withheld an unearned finish twice and
   recorded the mismatch honestly) - keep as-is.

== REVERT / RESTORE RECEIPTS ==
- FLIP receipt: staged-candidate/GROQ-FLIP-RECEIPT.json
  (before = 668da4f87348d1fa..., flipped = 14fd9164ad692928...)
- UNFLIP: the live v2_job_engine.py = byte-identical to the PRE-FLIP
  original (668da4f87348d1fa..., sha256-proved) + the adapter restarted
  (health ok, coding=True, providers=local-only) + jobs_registry._slot=None
  (a clean-path settle = released it; the surgery = the crash-era leak).
- adapter_token/.env/providers-config: never logged; no token printed.
"""
P = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
     r"\staged-candidate\RETURN-TO-MICA.txt")
open(P, "a", encoding="ascii", errors="replace").write(ADD)
print("[appended]:", len(ADD), "chars ->", P)