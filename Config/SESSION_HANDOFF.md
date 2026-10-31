# APEX - SESSION HANDOFF v2 (2026-10-31 02:10, pre-reboot, after full build + hardening)
Supersedes v1. Read this file first - complete state + exact remaining steps.

## STATE: build COMPLETE and hardened. All verified live.
- Apex root: C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed
- Adapter root: C:\Users\seaha\Apex-Adapter (companion.py + apex_hook.py + token)
- 29+ py files compile | 0 ps1 parse errors | 0 bare excepts in core | git history active
- Test suites: reward 8/8, memory 6/6, adapter 14/14, red-team 10/10
- Benchmark (real measurement): security 1.0, memory 1.0, learning 1.03, reasoning 1.0
  (calibration has live sample data), supervision 1.0, lanes 1.0 - unmeasured: []
- 28 attributes + critical thinking implemented with evidence: Config\GI_Attributes.md
- Dream task 'Apex-Nightly-Dream' 03:30: consolidation + benchmark + red-team + git-head
  checkpoint + overnight note (also written to Andrew's desktop as 'APEX overnight note.txt')
- Chat: APEX Chat.lnk on desktop -> ApexChat.pyw -> http://127.0.0.1:8080/talk (loopback ONLY)
- Dashboard: http://127.0.0.1:8080/ | Notes: /notes | Talk API: POST /talk/api
- Keys: Groq/OpenRouter/Gemini in .env (SEALED: Config/EnvSeal.json), local-first burst lanes
- Token: C:\Users\seaha\Apex-Adapter\adapter_token.txt (64 chars - NEVER print/display it)
  DELIVERED to Chad via encrypted chat 2026-10-31. Room watcher armed (room_watcher.py, 6h).

## REASONING CHAIN (in-plan order, all live)
1. DeepSeek plan (memory+ledger+curriculum+strategy informed)
2. Self-consistency votes: 2 Groq ballots, modal target, confidence-weighted
3. Socratic interrogation (ApexThink): assumptions/pre-mortem/falsifiers ->
   verdicts PROCEED / SHRINK / ABORT (aborts double-checked, then self-reject the plan)
4. Qwen writes: minimal-diff (adaptive by measured parity) or full rewrite, with guards
5. Critic pass (Groq hazard review) -> refinement if issues
6. Best-of-2 sandbox race: Groq alternate vs Qwen candidate
7. heal(): 3 trajectories, sandbox, reward gates (regression/no-op/behavior-loss/veto)
8. WRITE -> snapshot + git commit + skill certification + integrity seal + strategy update

## SECURITY STACK (all live)
- ApexGuard.py: FileIntegrity.json SHA256 manifest (boot-verified, tamper fails loud),
  EnvSeal.json (.env hash), redact_text (patterns + REAL .env values + injection flags)
- Evolution loop: loopback-only (127.0.0.1:8080), bridge 127.0.0.1:8081
- Vetoes: rmtree/system/popen/subprocess-destructive/ALIAS IMPORTS/GETATTR-all-forms/
  SHUTDOWN/logoff/CTYPES + eval/exec + deletion penalties - red-team drills 10/10
- Adapter: bearer token, 200KB caps, schema validation, duplicate registry (survives
  restarts), truthful cancellation, secrets scrubbed from ALL outputs (.env values too)

## THE ONE REMAINING MILESTONE: room connection (user-gated reboot happened?)
Andrew installed WSL2 (Default Version 2 staged) and REBOOTED (confirm: `wsl --status`).
Then execute IN ORDER:
1. Docker verify: `docker info` -> server version. If down: start Docker Desktop first.
2. `docker pull python:3.12-slim`
3. Acceptance tests: start companion (see below), run
   `python C:\Users\seaha\Apex-Adapter\test_local.py` (14/14 required),
   test #6 live-cancel (DELETE during a running request -> container killed -> 200),
   test #7 isolation (task reads host secrets -> container must fail to read them).
4. `tailscale serve --bg --https 9443 http://127.0.0.1:8788` - verify /v1/health,
   record base URL (no /v1/respond suffix) for Mica.
5. Andrew reads C:\Users\seaha\Apex-Adapter\adapter_token.txt LOCALLY and sends to Chad
   via encrypted chat. Mica sets APEX_APPROVED=1 + APEX_URL + APEX_TOKEN.
6. Room ceremony: real "@Apex" message -> honest reply -> Stop/cancel test -> small
   coding challenge. Then propose to Mica: lesson-packet + shared benchmark extensions.

## STARTING THE COMPANION FOR TESTS
$env:APEX_ADAPTER_TOKEN = (Get-Content C:\Users\seaha\Apex-Adapter\adapter_token.txt).Trim()
Start-Process <venv python> C:\Users\seaha\Apex-Adapter\companion.py -WorkingDirectory C:\Users\seaha\Apex-Adapter
run test_local.py, then stop the companion process.

## HARD RULES (never regress)
- HostGuard: never destabilize the host; reboots/killing user apps are human-only.
- Adapter token never printed/displayed. Unverified results are labeled UNEXECUTED.
- CORE_MODULES list protects Apex's own files from self-evolution.
- Evolution sandbox runs candidates on host-python TODAY; after Docker is alive,
  switch sandbox() to container execution (design exists, 1-line swap, gated).

## GOTCHAS (hard-won tonight - do not regress)
- NO WMI / Get-CimInstance / process enumeration in hot paths (hangs under churn).
  Registry + psutil + port checks only (Scripts/proc_check.py).
- No pattern-matching sweeps whose match text appears in the invoking command
  (self-match kills sessions). File-based helpers only.
- Dream re-seals files it legitimately writes (ApexSelf.json) - manifest stays exact.
- Log rotation + config lint + secrets-guard live in Boot-ApexShort.ps1.
- Adaptive lane order reads Apex-Adapter\Config\LaneStats.json (>= 5 samples per lane).
- Weakest-dimension computed over MEASURED dims only (no phantom 0.0).

## KEY FILES MAP
- Brain: run_apex_evolution.py (800+ lines, line-audited) | Bridge: optimized_agent.py
- Memory v2: ApexMemory.py | Guard: Scripts/ApexGuard.py | Pacing: ApexPacing.py
- Think: Scripts/ApexThink.py | Bench: Scripts/ApexBenchmark.py | Skills: Scripts/ApexSkills.py
- Collab: Scripts/ApexCollab.py | RedTeam: Scripts/ApexRedTeam.py | Research: Scripts/ApexResearch.py
- Versions: Scripts/ApexVersions.py | Dream: Scripts/ApexDream.py | Inspector: Scripts/proc_check.py

## SESSION END NOTE
Andrew's standing directive: every agent attribute, cutting-edge, within hardware
(i5-10400F/16GB/3050-8GB), never destabilizing the host. Build + security hardening DONE.
Reboot confirms WSL2. Then the room ceremony closes everything.
## 2026-10-31 ~05:30 - Apex V2 execution contract: implemented + acceptance rounds
- adapter: companion.py V2 routes live (POST/GET/DELETE /v2/jobs, artifacts manifest|zip), v2_contract.py + v2_job_engine.py (owner-approved backend), single-bind fix (allow_reuse_address=False)
- engine capabilities: bounded tool loop in disposable containers (--net none, --read-only, cap-drop ALL, no-new-priv, user 1000:1000, pids 96, mem 2048m, cpus 2), $0 local lanes, finish-gate honesty (withholds finish after failing run), cancel-ack hardened (_dc guarded docker, no rm-f hang), checkpoint seal/verify (sha256, <=200 files / 5MB), artifact ZIP manifest-v1
- acceptance: rounds 1-3 = 15 jobs (budget 10-15 reached), round-3 verdict 8/10 green; fail-closed gate (coding enabled=false, owner_approved=true) until targeted re-run of 2 pending items (RED run-through combo + DELETE ack <=8s); evidence: Apex-Adapter/acceptance_evidence.json + acceptance_run.log
- token discipline verified: 0 leaks across all responses/jobs/zips
- dream v3 (security-ops: pip-audit weekly + backup rotation + disk metric) and dashboard room-panel WIRED, re-sealed, live-verified
- APEX Chat: 100-prompt library inside chat (10 categories, clickable pills), clipboard bridge v2.1 - all sealed (manifest OK)
- adapter state: single listener 8788, watchdog+Sentry healthy, Mica room-side still staged/disabled pending Andrew's go

## 2026-10-31 ~06:15 - V2 ACCEPTANCE COMPLETE - coding enabled
- targeted re-probe green: RED run-through (exit 1 honest, claim-aware finish-gate), resumed GREEN (exit 0, hash-verified restore), cancellation DELETE ack 272ms (async kill + fast Engine-API runtime truth; was 10.5s)
- docker SDK 7.1.0 + pywin32 added (named-pipe Engine API; CLI fallback only) - in pip-audit scope now
- finish-gate hardened: withholds success CLAIMS after failing runs; honest red-finishes allowed
- gate final: owner_approved=true, acceptance_passed=true, health advertises coding enabled=true (owner_seat=friend)
- jobs total across all rounds: 23 executed, $0.00
- NEXT: Mica restarts room Apex client (their side approval flags) - first real @Apex coding round trip; evidence: Apex-Adapter/targeted_evidence.json, acceptance_evidence.json, mini probes
