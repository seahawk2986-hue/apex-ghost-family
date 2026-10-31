# Apex - General Intelligence Attribute Ledger
STANDING DIRECTIVE (user, 2026-10-31): every attribute below implemented with current
cutting-edge code, within hardware bounds (i5-10400F / 16GB / RTX 3050 8GB), never
destabilizing the host. Stored in ApexMemory (rule) and Config/ApexSelf.json (north_star).

Auditable mapping: every agent attribute -> implementation -> evidence -> status.
Hardware envelope: Core i5-10400F / 16GB RAM / RTX 3050 8GB. All items fit in-budget.

## 1. Identity & Self
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Persona | Stable name, purpose | room adapter identity, self card | DONE |
| Self-model | `Config/ApexSelf.json` — DYNAMIC: "measured" capability block refreshed nightly from real benchmark data (security/memory/learning/calibration/supervision scores + weakest dimension) | ApexSelf.json "measured" | DONE |
| Perception | Logs, ports, telemetry, peer directives + NEW-FILE DIFFING (notices environment changes incl. its own creations, feeds planner) | planner perception events | DONE |
| Core values | Honesty protocol + HostGuard restraint in semantic memory | `memory_semantic.jsonl` rules | DONE |

## 2. Architecture
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Perception | Logs, memory streams, ports, telemetry, peer directives | watchdog log, adapter /chat | DONE |
| World model | Sandbox pre-verification; per-file ledger; behavior-change calibration (predicted vs actual) tracked per strategy | RewardLedger calibration counters | RUNNING |
| Memory | Tier 1/2/3 (working/episodic/semantic) + consolidation + decay + dedup + hybrid fusion retrieval | ApexMemory v2, 6/6 tests | DONE |
| Reasoning engine | Hybrid: DeepSeek-thinks, Qwen-codes, nomic-embeds + self-consistency voting + Socratic interrogation + critic pass + Best-of-2 sandbox races | logs: votes/thinking/critique chain | DONE |
| Planning | plan() -> queue -> heal (3 repair trajectories) | planner.log locked targets | DONE |
| Tool use | winget, process supervisor, Docker, HTTP, model APIs | ApexInstaller, adapter | DONE |
| Execution isolation | Disposable Docker containers, network-isolated | adapter sandbox path | PENDING WSL2 |

## 3. Cognitive capabilities
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Learning | Multi-dim reward (syntax/safety/runtime/output-proof/progress), ledger bests, streak bonuses | RewardLedger + test_reward 7/7 | DONE |
| Reflection | Reflexion pre-brief assembled from recent events each cycle | plan() prompt | DONE |
| Critical thinking | Socratic interrogation before coding: assumptions surfaced, pre-mortem -> coder guards, falsifiers stated, verdicts enforced (proceed/shrink/abort with self-rejection) | ApexThink smoke test (4 unvalidated assumptions flagged on own success streak) | DONE |
| Metacognition | Honest degradation doctrine; never invents results; ensemble disagreement -> conservative coding | adapter "UNEXECUTED" path; ensemble line | DONE |
| Uncertainty | Skip-over unavailable engines; partial replies labeled partial; research notes labeled UNVERIFIED | hook engine chain + ApexResearch | DONE |
| Exploration/exploitation | Bandit-style neglected-file prior + reward-maximizing choice + self-issued curriculum | planner prompt + ApexSkills.curriculum | DONE |
| Skill acquisition | Certified skill registry distilled from reward-verified evolutions | SkillRegistry.json | DONE |
| Security self-testing | Red-team drills prove vetoes fire (rmtree/system/subprocess-rm/deletion penalty) | ApexRedTeam 4/4 | DONE |

## 4. Agency & Autonomy
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Initiative | At-logon boot of full stack | scheduled task + HKCU Run | DONE |
| Persistence | File-lock watchdog; zombie detection (port=truth); async boot | watchdog.log HUNG ZOMBIE kills | DONE |
| Self-modification | Evolution loop, minimal-diff first, core protection | ApexIPCEngine.py score-100 passes | DONE |
| Provisioning | HostGuard-governed winget installs | ApexInstaller + governor tests | DONE |
| Boundaries | Reboot/shutdown/kill-user-apps forbidden; CORE_MODULES protected | code + memory rule | DONE |

## 5. Social & Collaborative
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Communication | Contract-exact adapter (POST /v1/respond, DELETE cancel) | 14/14 local tests | DONE (local) |
| Theory of mind | `Config/PeerProfiles.json` peer-model loaded per reply (role/trust/style per peer) + unverified-output doctrine | adapter T7 honesty path | DONE (activated by room) |
| Honesty norms | Never claims unverified results | T7 round trip | DONE |
| Negotiation/division of labor | `Scripts/ApexCollab.py` deterministic work-split + handoff protocol, triggered by collaboration asks | module smoke test | DONE (activated by room) |

## 6. Safety & Governance
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Action gating | Write gate: 100 score, no regression, no no-op, behavior parity + eval/exec penalties + file-integrity manifest seals + boot tamper verification + ALIAS/GETATTR/SHUTDOWN/CTYPES vetoes | test_reward 8/8, ApexGuard verify, red-team 10/10 | DONE |
| Resource governance | Pacing brakes 60-600s; install governor; forbidden actions + HardwareGovernor per-cycle | pacing.log | DONE |
| Auditability | All decisions logged + episodic memory + live dashboard (GET 8080) + nightly dream report + git-backed evolution history (.env firewalled) + lane telemetry + log rotation | logs/, dream.log, .git, LaneStats.json | DONE |
| Revocability | Stop/kill paths; rolling snapshot + git revert; one-command rollback; token revocation | ApexVersions.rollback, git checkout | DONE |

## Integrity of the stack itself
| Attribute | Implementation | Evidence | Status |
|---|---|---|---|
| Hang-proof supervision | No WMI/process-enumeration anywhere in hot paths | registry + port-based checks | DONE |
| Single-instance | PID registry self-declaration | layer_pids.json | DONE |
| Self-match immunity | No cmdline-pattern guards | registry design | DONE |

Legend: DONE - implemented and verified. RUNNING - operating, accumulating evidence.
PENDING WSL2 / PENDING ROOM - requires Andrew's reboot / Chad's connection ceremony.