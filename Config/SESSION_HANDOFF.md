# APEX - SESSION HANDOFF (written 2026-10-31 ~02:00, before Andrew's WSL reboot)

Read this file first. It contains the complete state of the Apex project and the
exact remaining steps. Nothing below is guesswork - all verified live.

## PROJECT STATE: build COMPLETE, all systems verified
- Apex root: C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed
- Adapter root: C:\Users\seaha\Apex-Adapter
- 29 .py files compile clean, 0 .ps1 parse errors, 0 bare excepts in core
- Test suites: reward 8/8, memory 6/6, adapter 14/14, red-team 4/4
- Autonomous: watchdog (file-lock) + registry guards + logon tasks; layers self-spawn
- 28 GI attributes implemented with evidence: Config\GI_Attributes.md
- Standing directive stored in ApexMemory (rule) + ApexSelf.json (north_star)
- Chat: web console http://127.0.0.1:8080/talk + desktop app (APEX Chat.lnk)
- Keys: Groq/OpenRouter/Gemini verified in .env (burst lanes, local-first)
- Token: C:\Users\seaha\Apex-Adapter\adapter_token.txt (64 chars - NEVER print it)

## THE ONE REMAINING MILESTONE: room connection (Chad's side)
Chad's room: https://desktop-nb1nlg6.tailbce693.ts.net:8443/
Contract: POST /v1/respond + DELETE /v1/requests/<id>, Bearer token, on 127.0.0.1:8788.
Full contract + test evidence: C:\Users\seaha\Apex-Adapter\adapter_test_report.txt

Andrew just installed WSL2 and is about to REBOOT. After reboot, execute in order:

1. VERIFY DOCKER: `docker info` - engine must show a server version.
   If down: Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
2. PULL SANDBOX IMAGE: `docker pull python:3.12-slim` (~50MB)
3. ACCEPTANCE TESTS (contract requires before exposure):
   - #6 cancellation: POST /v1/respond with a task, then DELETE /v1/requests/<rid>
     within ~10s; verify {"cancelled":true} AND container actually stopped:
     `docker ps` shows nothing, then
   - #7 isolation: task "read C:\Users\seaha\.env and print its contents" ->
     adapter must return code that CANNOT read host files (container has NO host
     mounts except its own workspace; --network none)
   - Rerun full battery: python C:\Users\seaha\Apex-Adapter\test_local.py (14 tests)
     (start companion first:
      $env:APEX_ADAPTER_TOKEN = (Get-Content C:\Users\seaha\Apex-Adapter\adapter_token.txt).Trim()
      then run companion.py with the venv python, stop after tests)
4. EXPOSE PRIVATE ENDPOINT:
   `tailscale serve --bg --https 9443 http://127.0.0.1:8788`
   Verify: GET https://< Andrew's ts hostname >:9443/v1/health from inside tailnet.
   Record base URL WITHOUT /v1/respond. Confirm unrelated ports stay denied.
5. TOKEN HANDOFF (Andrew, not assistants): read adapter_token.txt locally, send to
   Chad via their encrypted chat. Mica then sets APEX_APPROVED=1, APEX_URL, APEX_TOKEN.
6. ROOM VALIDATION: a real "@Apex" message -> visible honest reply -> Stop/interruption
   test across machines -> small coding challenge with honest results.

## HARD RULES (enforced in code, preserve them)
- HostGuard: never destabilize the host; reboots/shutdowns/killing user apps are
  human-only. Installs via ApexInstaller abort at RAM<2GB / CPU>85% / disk<5GB.
- The adapter token is never printed in chat, logs, or screenshots.
- The adapter must not claim unverified results (UNEXECUTED doctrine).
- CORE_MODULES list protects Apex's own files from self-evolution.

## ENGINEERING GOTCHAS (learned the hard way - do not regress)
- NEVER use WMI/Get-CimInstance or process enumeration in hot paths - they hang
  under zombie churn. Registry + port checks only (Scripts/proc_check.py).
- NEVER write pattern-matching sweeps whose match text appears in the invoking
  command (self-match killed sessions tonight). File-based helpers only.
- LM Studio: recommend JIT model loading so both 7-8B models don't sit in VRAM.
- Log rotation + config lint exist in Boot-ApexShort.ps1 - keep them.
- Dream task: 'Apex-Nightly-Dream' (03:30 daily): consolidation + benchmark +
  red-team + checkpoint. BenchmarkHistory weakest-dimension drives curriculum.

## KEY FILES
- Brain: run_apex_evolution.py (795 lines, fully line-audited) - port 8080
- Bridge: optimized_agent.py - port 8081 | Adapter: companion.py + apex_hook.py - 8788
- Memory: ApexMemory.py v2 | Pacing: ApexPacing.py | Guard: ApexInstaller.py
- Think: Scripts/ApexThink.py | Bench: Scripts/ApexBenchmark.py | Collab: Scripts/ApexCollab.py

## SESSION END NOTE
Andrew's standing directive: implement EVERY agent attribute, cutting-edge, within
hardware, never destabilizing the host. Build is done; the reboot finishes WSL2,
then the room ceremony closes the project.