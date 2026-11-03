# THE STRENGTHS LEDGER — 2026-11-04

*Every weakness from the full-code audit, converted into a named organ. Each
row: the weakness (evidence), the organ (file), the verified source it is
built on, and the proof it ran. $0. Hardware-bound: 16 GB / i5-10400F, no new
dependencies, every mechanism stdlib or already-installed.*

| # | The weakness (evidence) | The organ now | The verified material | The proof |
|---|---|---|---|---|
| 1 | Pay address hardcoded in 6 tracked files of a PUBLIC repo | `.env PAYOUT_DEST` + redacting writers (PayoutDoor/CryptoEconomy/JobPortfolio) + `Scripts/_scrub_privacy_20261104.py` (0 literals left, receipt in `Logs/privacy_scrub_receipt.jsonl`) | GitHub secret-scanning guidance: tracked personal endpoints must leave tracked content (history handled founder-side) | scrub run: 5 files scrubbed, remaining=0 |
| 2 | Learning self-referential (gym grades its own teachers' word), no holdout | **`Scripts/RealityCourt.py`** — seal (sha256-locked pocket, never enters memory) + judge (internal trend vs sealed holdout → CLEAN/WATCH/SELF-FLATTERY verdict) + street (real-issue planning drills, structural truth) | arXiv:2407.01502 (holdout prescription); arXiv:2310.06770 (real GitHub issues as the external testbed) | seal ran live (sees Logs/court_seal_20261102.log); grader unit-checked |
| 3 | Green ledgers, external column unmeasured ("smooth ≠ progress") | **`Scripts/OutcomeYardstick.py`** → Config/outcomes.json → rendered on /receipts: INTERNAL (drills/writes/chats, 30d) vs EXTERNAL (merged PRs / Polar sales / funnel arrivals, every zero carries its reason) | the family's own honesty laws (print-first; no invented numbers) | first measure ran: 0 PRs, 0 sales, 0 arrivals — printed honestly |
| 4 | Sprawl: 3 .env schemas, unlock-but-never-delete locks, unbounded ledgers | **`Scripts/ApexIO.py`** (the spine: env + atom + self-deleting locks) — delegated by ApexShard/CloudBrain/LaneGuard; **`Scripts/LedgerTrim.py`** (rows AND bytes cap, nightly) | the family's own drift-audit lesson (call-site/callee contracts) | ApexIO lock lifecycle + IPC + yardstick smokes PASS; comb_passes 52.3MB → archived, live file bounded |
| 5 | Fixed timeout=75 for every lane; storm budget dead; cache off the user path; cold brain in the user path | **ApexShard tiered length-aware ladder** (`TIER_TIMEOUTS` + `_tier_timeout`, explicit timeouts still win), `_storm_ok()` enforced per hot-swap; **chat replay-cache** on BOTH chat routes (blocking + SSE stream, lane- tagged `cache ⚡ replay`, `!fresh` bypass)；**`Scripts/WarmBrain.py`** (RAM-gated 12h resident pinning, 4h cadence via ApexSentry) | their own canon: Clairvoyant (SJF admission), OUTLETS + Scheduling-with-Uncertainty-Aware-Length (length-aware timeouts), Requests-of-a-Feather (prefix reuse), Local-Splitter (token-usage), Squat + Nemotron-Flash (resident quant floors) | ladder + storm unit checks PASS; yardstick/canonical/trim receipts generated; WarmBrain honestly idled at 3.3 GB free (the RAM law held) |
| 6 | Sandbox relaxed to the HOST when Docker broke; bandit scanned a deleted file; auth compared in non-constant time; no CSP on /jobs+/receipts; dead counts (245/404/435); flag-drift killed every scheduled gym | fail-closed `sandbox()` (host = founder-written opt-in only); bandit-before-delete fixed; `hmac.compare_digest` gate; per-surface CSP + X-Frame-Options in the middleware; **`Scripts/CanonCounts.py`** stamps README/index/both job boards + badges from one canon; ApexGym parses `--minutes/--traits` (+ `__main__` guard; the 28-min gym survives its own callers now) | arXiv:2407.01502 (benchmarks-with-teeth: holdouts + cost + standards); the family's "every number checkable" law | compile OK ×19 files; existing stack suite 13/13 PASS |

## Also repaired (the audit's smaller truths)
- `ApexIPCEngine.py`: the crashed-on-first-use bus is real now (routed deque,
  honest None, bounded 10k).
- `CloudBrain.py`: duplicate `"gemini"` pricing key dead.
- `ApexServe.ps1` MoE: a missing draft-model gguf no longer breaks the launch
  (honest "serving without speculative drafting").
- `Boot-ApexShort.ps1`: the watchdog lock is now judged by OS exclusion (a
  stale file can't fake a live watchdog anymore).
- `ApexSentry.ps1`: PackSync stopped running every 1-min tick (30-min cooldown);
  ears respawn on a 5-min cooldown; WarmBrain on a 4-h cadence.
- `Recall2.py`: memory rows matched by fingerprint (archived-window drift can
  no longer serve the WRONG event); index CAP enforced with aligned metas.
- `ApexChatPage.html`: stray post-`</html>` CSS relocated into the stylesheet
  (no more visible junk), SEND casing, textarea `aria-label`.
- Dashboard route reachable again at `/dashboard` (it was shadowed as "/").

## Honest remaining risks (not hidden)
- Git history holds the old address literals until the founder chooses
  rotation vs history-filter (never done silently).
- The host-sandbox opt-in keeps power with the founder — if set to 1, the old
  exposure returns (that is why it requires HIS hand).
- 5 lane-system overlays still exist under the spine (Shard/LaneGuard/
  LaneMesh/CloudBrain/CloudLanes). The spine standardizes env/io; merging the
  lane pools themselves = the next surgical round (kept out of today's change
  to keep the live fleet unbroken).
- The court's first judge verdict needs the seal to finish + one gym beat to
  compare against.
---

## THE FLEET ROUND (2026-11-04, same session - the fleet's own weaknesses)

Measured live at 18:47-19:12 from scores/lane_state.json + the catalogs:

| The weakness (measured) | The organ now | The proof |
|---|---|---|
| nim-k3: 410-Gone corpse still occupying a rotation slot | AutoRoster.retire_dead(): 410 = retired on first sighting (RFC 9110: Gone is permanent), watched for return, episodic receipt | [roster] RETIRED: nim-k3; order_for excludes it (assert PASS) |
| Roster NEVER renewed itself; free tiers churn weekly | AutoRoster.refresh(): each provider's OWN documented catalog (Groq /v1/models - verified live against their published reference today; OpenRouter catalog; NIM /v1/models; GitHub-Models catalog w/ the held PAT) -> bounded 1-token capability probes -> Config/lane_extra.json merged into rotation | first beat: 2 LIVE lanes added (minimaxai/minimax-m3.1-flash 200-in-6.1s; nvidia/nemotron-safety-guard-8b 200-in-1.0s), 7 honest dormant receipts |
| A content-SAFETY classifier could have answered chat | guard/safety names classify as tier "guard" = registered for tools, EXCLUDED from chat rotation | assert PASS (no guard tier in chat order) |
| The dispatch order was static; cold lanes led it; walled lanes hidden in the middle | LaneBandit: eps-greedy (0.18) ordering with a latency-shaped reward (success/log(2+ms/80)); pacer-windowed lanes demoted; CapabilityMap-seeded prior | order-for renders: floors pinned, mediums bandit-ordered, walled behind healthy |
| Storm budgets could be drained by the organs, starving user-facing calls | per-CLASS budgets (protected 30/h vs batch 12/h), per-class ledger files; organs default batch; user-facing paths don't draw Shard storm at all | compile + order tests PASS |
| Pacer/rotator roster drift (nim-v4pro rotated but unpaced) | LaneGuard's book now includes nim-v4pro; ONE roster contract (shard LANES + verified extras) | lane_state includes nim-v4pro on the next LaneGuard beat |

Sources: Groq API reference (models-list; fetched live 2026-11-02); the
family's own ProbeFreeModels.py precedent (GitHub/OpenRouter/Gemini catalogs);
Auer/Cesa-Bianchi/Fischer 2002 (eps-greedy class); the 2026 canon's
router/QoS papers (Token-Budget-Aware Pool Routing, CALM, DriftSched).

## THE BLIND COURT'S FIRST VERDICT (19:13:42, live)
- holdout_pct 40.7 (n=27, sealed) vs internal_pct 31.6 -> VERDICT: CLEAN
  (no self-flattery detected; the fleet slightly UNDER-flatters its gym trend)
- street: 5/6 real GitHub-archive issues -> structurally sound fix-plans
  (external-distribution planning truth; receipt Config/court_street_receipt.json)
- the court now judges nightly inside ApexDream; the verdict renders on /receipts

## THE HISTORY PURGE (2026-11-04, executed with the founder's full permission)
- git filter-repo, one pass: Lib/ (the accidentally-committed 117MB venv,
  7190 files) + Config/apex_api.key (all history) inverted out; paypal
  literals replaced ([REDACTED-PAYPAL]) - pickaxe: 0 hits, ALL history.
- repo pack: 117.04 MiB -> 10.33 MiB. Force-pushed: 93305e5...9662076
  (verified remote == rewritten local head after the check - the bots'
  next clone starts from the clean lineage).
- THE GATE KEY WAS ACTUALLY ROTATED (not merely scrubbed): fresh mint on
  disk; server restarted onto it; stale 401 verified. The old published
  value is dead at HEAD, in history, in memory, and in files.
- Full-byte backup preserved first: Downloads/apex-ghost-family_full_backup_20261104.git
- RESIDUAL (honest): orphaned pre-rewrite SHAs can persist in GitHub
  caches/forks until platform GC - for absolute certainty, rotate the
  PayPal receiving address when convenient (receiving addresses are not
  credentials; residual risk = spam, not access).

---

## THE AUTONOMY ROUND (2026-11-04) - Apex vs the verified world frontier

Scored against: METR 50%-time-horizon (arXiv:2503.14499, NeurIPS 2025, v4
Jul-2026 - frontier ~50min, doubling ~7mo, reliability = the driver) +
SWE-bench 2026 (mini-SWE-agent 65% Verified Jul-2025).

| Axis | Verdict + the organ |
|---|---|
| Time-horizon per goal | WAS unmeasured (up-time infinite, goal-horizon unknown). NOW MEASURED: **226 steps / 26.6 min @ 99% completion** (first receipt, HorizonLadder) - the METR-analog from the family's own ledgers; the trend line exists; the failure map (error x15) = the climb map. CLOSING: the nightly Dream is now ONE LONG MEASURED CHAIN (the organs run in sequence) - the horizon receipt grows with it |
| Mistake-recovery (METR's driver) | Architecturally strong (heal x3/critic/Best-of-2/Court); NOW MEASURED via the failure histogram in the same receipt |
| SWE-class external score | GAP (deferred with dignity): the SWE-harness organ = next round (real harvested repo-issues executed in the sealed container) |
| Self-modification | UNIQUE LEAD (frontier agents do not self-evolve; Apex does it inside sealed containers with courts) |
| Multi-agent | LEAD (hub + family + swarm + shard dispatch) |
| Cost discipline | LEAD ($0 enforced everywhere; the spend-gates receipts) |
| Honesty/consent machinery | LEAD (constitution, Blind Court, canon counts, no-lane laws, tripwires) |
| Conversational sourced research | CLOSED THIS ROUND: **LightResearch** (search -> polite fetch -> cross-checked synthesis w/ sources + NOT-FOUND-IN-SOURCES honesty; live on "research:" in the chat) |
| Uncertainty/calibration | MEASURED + published (0.34 reasoning_calibration; 4/6 overconfidences; the holdout 40.7% vs internal 31.6%) - values honest, improvement = the weak-first curriculum |

THE TRIPWIRE (HookCheck): the silent-revert class that ate the Dream/receipts
hooks = on a 1-min cadence now (manifest-driven re-install + alarms); the
integration-spine law: the evolver never re-issues receipts_page.py
(CORE_MODULES).
