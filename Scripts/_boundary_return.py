"""THE BOUNDARY RETURN-RECEIPT: exactly what Micah's cover-note asks to
return = staged/deployed hashes + the NEW nine-test evidence + the
existing synthetic evidence pointers + the honest divergence notes.
A single compact TXT (no archive, per the note)."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
OUT = ROOT + r"\staged-candidate\RETURN-TO-MICA.txt"

rec = json.load(open(ROOT + r"\staged-candidate\STAGE-RECEIPT.json",
                     encoding="utf-8"))
arch = "f979f029a6fa5291eccec76b5d1dc08bd73eaca9fe4b36d320c6e2be5fa8c946"
base = rec["stagedFiles"]

txt = f"""APEX V1 CHAT-BOUNDARY - ANDREW-SIDE RETURN RECEIPT
ts: {time.strftime("%Y-%m-%d %H:%M:%S")}
delivered archive: Apex-V1-Chat-Boundary-STAGED-20261102.zip
archive SHA256: {arch}   (byte-exact MATCH at intake)

== SOURCE STATE ==
live-shape 4-file revision (companion+v2_job_engine+v2_contract+
v1_chat_boundary, name\\0bytes\\0): {rec["live_shape_4_file_source_revision"]}
package baseRevision (for reference): dba5ef5ebe087c51f5ce5fb37e4adc4668ba5abca99c3d58272bbcd530ca48c3
package sourceRevision: 9959623d7d0710a22b21493f68692755e5fc22d3df3d7b44517762b08cacc026
STAGED 13/13 = MANIFEST-verified; staged companion = YOUR BASELINE,
live companion = EVOLVED (28,890b vs 22,096b): live holds newer work
(bounded artifact-ZIP builder + credish-guard + richer container-truth).
Per your instruction: NO full-baseline overwrite. The live-shape staging =
live files + surgical hunks ONLY.

== APPLIED (STAGING ONLY - NOTHING INSTALLED, NOTHING ACTIVATED) ==
1. companion.py (LIVE copy) hunks A+B: +import v1_chat_boundary;
   apex_hook.respond(req,cancel) -> v1_chat_boundary.dispatch(apex_hook,...)
   Hunk C (comment-only) SKIPPED: its anchor text is absent in the evolved
   live file; semantic effect = zero (it changed only explanatory comments).
2. v2_job_engine.py: UNTOUCHED (live = monolith 69KB evolution; the patch's
   source_revision hunk targets your 7-file split-engine baseline which the
   live shape no longer matches; live has no source_revision function).
3. v2_contract.py: UNTOUCHED (live copy byte-identical to package).
4. The package's 5 split-engine modules (v2_state/v2_sandbox/workspace_io/
   v2_inference/v1-patch-hunks): N/A to the live architecture; reviewed,
   MANIFEST-verified, not deployed.

== THE ACTUAL HOOK (your prepare_hook_patch.py, owner-local input) ==
input  apex_hook.py (LIVE, real URLs/models/keys) sha: f335633faedeaff2ba085d97f836c7fe1fe9426958ff35ca4542909cbcf5ffa3
output apex_hook.chat-only.STAGED.py sha: {base.get("apex_hook.chat-only.STAGED.py", "d67e06f17f6e164ea61cac661c877d93141b33caf2024e39cf08a85f7086b302")}
transform exit=0, installed=false, executedHook=false
diff = +13/-218: the 218-line executing respond body REPLACED by the two
chat-only wrappers (respond -> respond_chat; policy apex-v1-chat-only-1);
provider helpers (_generate/_remaining/_Ctx/_OutOfTime/time) untouched;
REAL urls/models/keys preserved (no sanitized placeholders installed).
Secret-leak scan on diff additions: CLEAN.

== STAGED FILE HASHES ==
""" + "\n".join(f"  {v}  {k}" for k, v in sorted(base.items())) + f"""

== NINE FOCUSED BOUNDARY TESTS - RUN (with Andrew's approval, 2026-11-01) ==
env: docker image apex-sandbox:latest id 37dc38177d3c (owner-approved,
existing - no pull), 1 CPU, 512MiB, --network none, NO host-mounts (files
injected via docker cp), no credentials, no real providers, container rm'd.
runner: python /tests/test_chat_boundary.py
exit: 0 | Ran 9 tests in 0.001s | OK (9/9)
 1 test_fenced_code_is_only_text               ok
 2 test_markup_tool_call_is_only_text          ok
 3 test_execution_fields_cannot_promote_v1     ok
 4 test_unpatched_legacy_hook_is_never_called  ok
 5 test_missing_policy_is_fail_closed          ok
 6 test_marked_inference_entry_preserves_reply ok
 7 test_cancel_before_inference_never_calls_provider ok
 8 test_late_provider_reply_is_discarded       ok
 9 test_transform_preserves_real_config...     ok

== PRIOR EVIDENCE (preserved, not dismissed) ==
- 18 fixture unit tests OK (3.04s) on sourceRevision dba5ef5e (your
  fixture-tested revision) - rerun on Andrew's machine, documented.
- sandbox end-to-end (create/run/fail/inspect/fix/pass/export + physical
  child-cancel + confinement-inspect) exit=0 x3 on apex-sandbox:latest
  (37dc38177d3c): in C:\\Users\\seaha\\OneDrive\\Desktop\\Chad.zip
  (sha 8821e102beab3a586ee2bf4e833fb0d48d6d86c938ca513168f5641e9e22dc78),
  notes on the image-pin difference cf71e96 vs 37dc38 included there.
- NOT rerun: the 18 (per your no-broad-repeat note).

== STATE / GATES (honest) ==
- LIVE adapter: untouched (backup: C:\\Users\\seaha\\Apex-Adapter-Backup-
  pre-boundary-20261102). Chad's room coding flag: OFF. Credentials,
  network, routes: UNCHANGED.
- V1 chat-only: staged + 9/9-proven in fixture; activation = after the
  real acceptance, per your coordination note.
- Real-model V2 acceptance: NOT RUN - awaiting Andrew's explicit route +
  disclosure consent (asked; not invented).
- No acceptance_passed claim anywhere. No spend ($0.00).
"""
open(OUT, "w", encoding="ascii", errors="replace").write(txt)
print("[return receipt]:", OUT)
print("[bytes]:", os.path.getsize(OUT))