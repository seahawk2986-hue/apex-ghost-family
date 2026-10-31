# Apex Agency Framework — task ledger (Andrew directive, 2026-10-31)
Six capability bullets → what Apex already does (measured) → upgrade shipped today →
next-level items queued. Everything constrained to: 16GB/i5-10400F/RTX3050-8GB, local
lanes, $0, HostGuard pacing, no host destabilization.

## 1. Cross-Domain Generalization
- NOW: transfer drill exists in the prompt library; skill registry stores certified
  skills per file; episodic+semantic fusion retrieval.
- SHIPPED TODAY: **pattern extraction** — nightly dream distills certified skills into
  `Config/Patterns.json` (domain-agnostic summaries); the V2 engine retrieves patterns
  relevant to a new task's objective and injects them as context ("applicable
  patterns") so a coding-certified pattern can inform a non-coding task.
- NEXT: pattern-level eval (transfer success rate as a benchmark dimension).

## 2. Autonomous Task Synthesis
- NOW: nightly dream picks weakest benchmark dimension; curriculum queue feeds drills.
- SHIPPED TODAY: **self-synthesized task DAG** — the dream generates a prioritized
  3-subtask plan (via the local model, JSON) from its own operational gaps, persists
  `Config/TaskDAG.json`, and each session can execute the cheapest next sub-task.
- NEXT: execute DAG fully autonomously inside the dream (within wall/budget caps).

## 3. Dynamic Learning & Plasticity
- NOW (honest wall): weights are frozen — "learning" today = episodic/semantic
  consolidation + strategy memory + calibration grading; consolidation can forget.
- SHIPPED TODAY: **anti-forgetting pinning** — consolidation refuses to prune episodes
  referenced by certified skills or committed forecasts (pinned set).
- NEXT (Andrew approval held): LoRA fine-tune on curated episodes (8GB-tight, offloaded
  training) — true weight plasticity; queued as its own approved project.

## 4. Metacognition & Self-Correction
- NOW: finish-gate (withholds success claims after failing runs), self-reject on
  failed specs, best-of-2 races, SAST vetoes, red-team drills, forecast calibration.
- SHIPPED TODAY: **critic-verify loop in the V2 engine** — on finish after a passing
  run, one extra model call cross-examines "does the final output satisfy the
  objective?" → mismatch nags the model once, second mismatch = job honestly `failed`.
- NEXT: adversarial self-play (best-of-N with critic scoring inside one budget).

## 5. Abstract Reasoning & Spatial-Temporal Planning
- NOW: forecast/parity doctrine; plan-then-act demanded in the coding system prompt;
  reason drills in the library.
- SHIPPED TODAY: **plan events are first-class** — the V2 engine's first accepted
  action must be a plan (logged as a status event before any tool call), and the
  driver/test asserts its presence; risk framing (anticipate-then-mitigate) added to
  plan format.
- NEXT: DAG plans spanning multiple sessions (ties to #2).

## 6. Tool Synthesis & Environmental Manipulation
- NOW: bounded built-in tools (files/exec/tests) in a disposable container; approved
  external compute lanes (Groq/OpenRouter) for inference; no host tooling.
- SHIPPED TODAY: **tool-synthesis hint loop** — on an unknown/unsupported action the
  engine coaches the model to BUILD the missing capability as a workspace script and
  run it (self-made tools live and die inside the disposable container).
- NEXT: synthesized-tool reuse across a job via a tools/ convention; skill-capture of
  a useful synthesized tool back into the registry (owner-reviewed).

## Status
- All "SHIPPED TODAY" items are implemented and compiled; engine items verified by a
  live coding job asserting plan + verify events.
- Honest walls documented: frozen weights (until LoRA approval), single-active-job,
  local-lane latency on partial offload.
## OPEN CARRY LIST (addendum from Directives Audit, 2026-10-31 ~06:15)
- [ ] Council live-fire success row (directive-upgraded nag deployed; auto-verified next suite)
- [ ] Pack version-bump rebuild (engine hashes moved past shipped pack; queued behind suite)
- [ ] Micah folder refresh with rebuilt packs
- [ ] ApexSelf identity confirmation via live chat (engines block rewritten 2026-10-31)
- [ ] Ears: spoken end-to-end test on grammar build (Andrew); dictation quality beyond SAPI (upgr. path)
- [ ] LoRA weight-plasticity project (APPROVAL-GATED by Andrew)
- [ ] Multi-session DAG execution (designed)
- [ ] Transfer-success-rate benchmark dimension
- [ ] Room activation: Mica/Chad restart after pack review (external party)
Compliance audit: Config/DirectivesAudit.md (25 directives, 22 closed, carry list above).

## HYBRID BRAIN ROUTING (Andrew approved 2026-10-31 ~06:5x: "yes we will use the best weight for the best jo
b")
- Purpose-routed brains with TIME-SHARE discipline (never stack big models; RAM wall 16GB total):
  chat/reasoning -> Qwen3-30B-A3B MoE (download started; quant chosen for RAM fit at load test)
  V2 coding -> qwen2.5-14b-instruct (resident) | offline chat fallback -> qwen3-8b
  QLoRA specialist -> trained on Andrew-discourse + gym-graded examples (separate py3.12 venv via uv;
    torch/peft/bitsandbytes; trains ONLY while other models are unloaded; eval via gym scorecard
    BEFORE promotion; swap needs Andrew approval)
- HostGuard: RAM brake rules training start (abort < 2GB free); MoE sessions unload other models
- Honesty: candidate brains must beat incumbent on GymScoreboard before promotion (ledger records rank)


## CHAT-TRIGGERED AUTONOMY + IDLE DRIVE (2026-10-31 ~06:3x) — shipped
- Apex can now ACT from his own chat: 'run the gym' -> gym spawn; 'harvest/farm/seek' ->
  curiosity drive spawn; 'skill session' -> python-semantics drills; 'library stats' ->
  live library summary. Each spawn is bounded (3-5 min) and rewarded.
- Sentry idle-driven autonomy: every minute, when RAM > 6 GB free and cooldown (2h)
  passed, Sentry spawns either a 5-min gym round or a 5-min curiosity farm - rotating.
  Boundaries binding: HostGuard RAM brake still rules; critical system files NEVER
  written by Apex; the V2 container stays network-isolated; all autonomy bounded and
  logged (Logs/sentry.log + episodic rows).
- TaskDAG execution loop: DAG synthesis runs in the dream; executing proposed DAG items
  as drills is the next queued build.
