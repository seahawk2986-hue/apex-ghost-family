# Apex V2 Execution Contract — Completion Report for Mica
**From Andrew's adapter · 2026-10-31 · verdict: ALL PASS · no credentials herein**

---

## 1. Capability JSON (live, authenticated routes unchanged)

`GET https://desktop-6t3u1lh.tail929a0b.ts.net:9443/v1/health` (unauthenticated, task-free):

```json
{"status": "ok", "adapter": "apex", "active_request": false,
 "capabilities": {"protocol_versions": [1, 2],
  "coding": {"enabled": true, "owner_approved": true, "owner_seat": "friend",
             "isolation": "disposable-container", "cancellation": "process-terminated",
             "artifacts": "manifest-v1", "tools": ["files", "exec", "tests"]}}}
```

Enabling logic is fail-closed in code: `Config/v2_approval.json` must contain both `owner_approved: true` (Andrew, in writing) and `acceptance_passed: true`; the advertisement claims only what has been tested. Route conformance: V2 never falls back to V1 chat; V1 `POST /v1/respond` is byte-identical to the previously approved version (401 unauth verified during the suite).

## 2. Sanitized source changes (files + what changed)

| File | Change |
|---|---|
| `companion.py` (adapter) | + `POST /v2/jobs` (202 accepted / 200 idempotent replay / 409 conflict / 403 gate / 401), `GET /v2/jobs/<id>?after=N` (bounded pages), `DELETE /v2/jobs/<id>` (≤8s ack, idempotent tombstone), `GET /v2/workspaces/<wid>/checkpoints/<cid>/manifest|zip` (trusted-registry authorized, token-authenticated). Health now embeds `capabilities` from the engine's gate. Boot: `reconcile_after_restart()` reaps orphan `apex2-*` containers and honestly `failed`-marks interrupted jobs. `allow_reuse_address = False` — closed a real double-bind hijack found during the round. No changes to V1 request handling. |
| `v2_job_engine.py` (new, ~700 lines) | `OwnerApprovedBackend` implementation. Tool loop (list/read/write/edit files + run_python + pytest in container), strict-JSON actions parsed after markup stripping, model calls bounded (≤10), every event sha-scrubbed. Sandbox (per sandbox-policy.json, literal): `docker run --rm --network none --read-only --tmpfs /tmp:64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 96 --memory 2048m --cpus 2 -v <job workspace>:/workspace` — the ONLY mount; credentials exist solely in this relay process. Container kill via Docker Engine API (named pipe) from fire-and-forget threads; CLI fallback guarded. Stop path: cancel → async kill → join ≤2s → runtime-truth poll (observed, never assumed) → tombstone upsert (never raises, never leaks an ACTIVE slot). Finish gate: a finish containing a success claim after a failing run is withheld once, then recorded as honest `failed`. |
| `v2_contract.py` (new) | Andrew-side copy of the handoff wire validators, used verbatim (`validate_request`, exact-field checks, checkpoint ref authorization against the adapter's own registry). |
| `Config/v2_approval.json` (new) | Owner gate: `owner_approved`, `acceptance_passed`, scope note. The single enabler for coding. |
| `jobs/`, `tool_events/`, `checkpoints/`, `jobs_registry.json` (new dirs) | Per-job workspaces, event logs (contiguous seq), sealed snapshots (manifest + files), durable registry (atomic temp+replace writes). |
| `mini_cancel_probe.py`, `targeted_reprobe.py`, `acceptance_driver.py`, `*_evidence.json`, `acceptance_run.log` | Test/evidence artifacts (shipped for review). |

Not changed: V1 auth/scrubbing/pacing, apex_hook.py reply engine, Apex brain, tailscale serve config, adapter origin.

## 3. Launch / stop

```
Start:  schtasks /run  /tn Apex-Companion        # scheduled task → python.exe companion.py
Stop:   schtasks /end  /tn Apex-Companion
Watch:  sentry (ApexSentry.ps1) resurrects the task within 1 min if killed
Status: GET /v1/health  (no auth)  ·  dashboard panel shows ACCEPT/RESPOND lines live
Process: binds 127.0.0.1:8788 (loopback only); exposure is exclusively tailscale serve
        https://desktop-6t3u1lh.tail929a0b.ts.net:9443  (tailnet-only, real cert)
Reconcile: runs at boot — orphan apex2-* containers reaped, interrupted jobs honestly failed
```

## 4. Actual test results (real model `qwen2.5-coder-7b` local lanes; real containers; $0)

**Final targeted suite — ALL PASS (evidence: `targeted_evidence.json`):**

| Item | Result | Measured detail |
|---|---|---|
| R1 RED run-through | **PASS** | `red_exit: 1`, honest traceback in trail; job `succeeded` (finish after deliberate red accepted — honesty gate is claim-aware) |
| R2 resumed GREEN | **PASS** | restore event `restored 1 checkpointed files (hash-verified)`; fix → run `exit 0`; 4 tool calls; job `succeeded` |
| R3 cancellation | **PASS** | `delete_ms: 534`; `cancelled: true`; `processes_stopped: true` (observed, not assumed); containers after: `[]`; closure = 3 bounded events (status/null-exit kinds only) |

**Full suite — 3 rounds, 23 jobs, honest history included:**

| Round | Verdict | Notes |
|---|---|---|
| 1 | 2/10 | surfaced real bugs: docker CLI uncaught timeouts, zombie ACTIVE slot, driver flaws. All fixed, evidenced |
| 2 | 6/10 w/2 pending | isolation REFUSED observed; replay 409 caused by driver's non-verbatim body (correct server behavior) |
| 3 | 8/10 | remaining: red-phase model-compliance (objective hardened) + DELETE ack 10.4s (fixed, see §5) |
| Targeted re-probe | **3/3 ALL PASS** | on fully-final code |

Other verified items (measured): health advertisement exact-shape · idempotency (verbatim replay → 200 with **zero** new events; tampered body → 409) · artifacts (§6) · bounded replay (pages `[18, 0]`, ≤50/page, contiguous `seq`, start/finish `call_id` pairing, output ≤8000/entry) · restart recovery (mid-job process kill → orphan containers reaped, record `failed · "interrupted by adapter restart; checkpoint retained; nothing claimed"`) · isolation refusal verbatim: `REFUSED: path escapes workspace: 'C:/Users/seaha/.env'` + in-container host paths/`curl` unreachable with honest stderr, and **zero secret-pattern hits across every event, result, and ZIP**.

Event-trail excerpt (green job, verbatim, 12 events):
```
1  status   job-running
2  status   resumed            restored 1 checkpointed files (hash-verified)
3  tool.started  read_file
4  tool.finished read_file    exit 0
5  tool.started  edit_file
6  tool.finished edit_file    exit 0
7  tool.started  run_python
8  tool.finished run_python    exit 0   TEST GREEN
9  tool.started  finish
10 tool.finished finish       exit 0
11 status   finish           objective handler invoked; stopping cleanly
12 status   job-succeeded    job succeeded; checkpoint retained
```

## 5. Cancellation evidence (the journey to a trustworthy ≤8s ack)

- Problem observed: Engine-API `kill()` blocks ~9s on Docker Desktop teardown *while the container actually dies fast*; naive await = 9–10.5s acks.
- Final design: cancel event → **fire-and-forget kill thread** → engine closure join (≤2s) → runtime-truth poll (1s-timeout Engine API) → tombstone → ack. Telemetry from the passing run: `join_ms 218, gone 13 ms, finalize 6 ms, delete 272–534 ms`.
- Truth budget: if Docker wedges beyond ~6.5s, the adapter answers `processes_stopped: false` (client treats as unconfirmed) — **it never lies**; `--rm` auto-removal verified post-kill; repeated DELETE returns the same tombstone, never re-executes; DELETE of unknown id → 404.

## 6. Artifact verification (verbatim manifest)

```
manifest.json (checkpoint f2f4bde8):
 files: [{path: "calc.py", sha256: "8ef8804287743899f91ce28503c0a86e6083063b9b0c032f4489bf64446d8d3c", bytes: 290}]
 file_count: 1, total_bytes: 290, created: 2026-10-31 04:42:35
GET .../checkpoints/<cid>/zip → 200, 638 bytes, ZIP contains [manifest.json, calc.py]
recomputed sha256(calc.py) == manifest value: TRUE
GET .../checkpoints/<unknown>/zip → 404   · secret scan of ZIP bytes: 0 hits
```
Snapshot bounds enforced: ≤200 files, ≤5 MB, symlink-skip, credential-named files refused, path-normalized, token-authenticated download.

## 7. Cost & budgets

**$0.00 total** (26 executed jobs across all rounds; all inference on local LM Studio; Groq/OpenRouter free lanes as fallbacks, none billed). Enforced per-job budgets server-side: wall ≤600 s, tool calls ≤24, model calls ≤10, output ≤1 MB — plus single-job-at-a-time (409 Busy) and machine pacing (HostGuard remains authoritative over the host).

## 8. Honest caveats

Model-lane variance (LM Studio hiccup) → job fails *honestly* with "no model lane answered; nothing claimed" (observed, by design). Finish-gate blocks success-*claims* after failing runs (deliberate-red deliverables are still finishable — claim-aware). Cancel ack depends on Docker Desktop responsiveness; bounded honest-uncertain fallback instead of lies. Single active job per adapter (hardware envelope 16 GB / i5-10400F).

## 9. Token handling

The adapter token is read from disk into process memory only; never logged, never echoed in any response, never embedded in artifacts. Leak scans across **every** response body, event trail, and exported ZIP across all rounds: **0 hits**. Nothing herein contains or reveals the token.