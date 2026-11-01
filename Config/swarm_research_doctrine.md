# Swarm Research Doctrine — scraped from arXiv, 2026-11-01

Source: export.arxiv.org API (cs.MA, "multi-agent LLM", "agent swarms"), 17 entries,
634 totalResults / 115 totalResults confirmed. Semantic Scholar API returned 429
(rate-limited) - noted honestly. Every doctrine below cites its paper.

## D1 — The Coordination Tax (Zettl & Gosmar, arXiv:2610.37700)
Planner-coder-reviewer pipelines cost 3.22x a single strong call, run 3.24x
longer, and solve NO MORE tasks. The win is model-per-task choice (94.3% at half
cost per solved task). ADOPT: decompose only when a break-even estimate clears;
else one good call. Measure every extra organ's wall-time against its yield.

## D2 — Failures are coordination failures, not capability failures (arXiv:2610.32060)
3,211 failed multi-round trajectories: failures dominated by recovery/consensus
problems that BEGIN after peers see each other; minority-signal suppression is a
named killer. ADOPT: disagreement handling + evidence verification + recovery
checks before finalize; keep the explorer share (minority preservation) sacred.

## D3 — Compact fact exchange beats sharing traces (REMAP, arXiv:2610.34836)
Gains concentrate where each agent holds DIFFERENT evidence; fact-level exchange
improves alignment AND cuts overhead vs full-trace sharing. ADOPT: GrainLine
manifests carry verified facts (mine/sha/grade/evidence) with explicit acceptance
conditions (AutoSwarm, arXiv:2610.33048) - never raw transcripts.

## D4 — Herding: measure EXCESS convergence (Trading Swarms, arXiv:2610.37448)
Communicating swarms converge beyond the no-peer baseline (7pp phrase copying).
Convergence is a RISK, not a goal. ADOPT: a diversity guard - if dedup or shared
notes collapse lane diversity, alarm it like the regression alarm.

## D5 — Experience synthesis at birth (ReGE, arXiv:2610.33861)
ONE coach call over bounded execution records produces guidance that lifts fresh
attempts ~9-10pp at a fraction of the tokens. ADOPT: child-spawn synthesizes the
round's records into bounded guidance instead of inheriting full raw histories.

## D6 — Recombine, don't imitate (SwarmRSI, arXiv:2610.20431)
Feedback-guided mutation + COMPLEMENTARY recombination of partial results across
agents beats pure best-lineage copying. ADOPT: family selector keeps complementary
lineage params (partial wins recombine) - not just champions.

## D7 — Bids beat static caps (MPT, arXiv:2610.22322)
Agents that BID willingness (and locally feel collective outcomes) self-orchestrate
better than fixed structures, scale, and survive dropout. ADOPT: ghost scheduling
by bid (fitness x urgency x RAM headroom) replaces static semaphore floors.

## D8 — Fail-closed supervision, signed heartbeats, short leases (Enclawed, arXiv:2610.33318)
Launch gates refuse what they cannot parse; signed heartbeats grant short leases;
evict on evidence; 12/12 live attacks ended fail-closed. ADOPT: sign ApexGuard
heartbeats, expire leases hard, evict on evidence.

## D9 — Convergence narrows the information space (RIVER, arXiv:2610.32333)
Pooled interaction converges but narrows; distributed relay broadens. ADOPT as a
measured property: track convergence/exploration/retention on the family's own
round outputs - the swarm knows when it is inbreeding.

## D10 — Serving reality: coordination workloads expose bottlenecks (MAServeBench, arXiv:2610.40293)
Collaboration patterns themselves determine serving/hardware bottlenecks. ADOPT:
the swarm's RAM/serving budget (2.2GB law, 32MB workers, one resident brain) is a
FIRST-CLASS dimension of design, not an afterthought.

## Context for later
- MOSAIC (arXiv:2610.35934): decentralized swarms DID outperform isolated experts
  on open-ended discovery - the premise holds when evidence is distributed.
- Context Language Models (arXiv:2609.37725): context-as-file + model-managed
  memory = large efficiency gains on 24h swarm tasks - aligns with tiered memory.

---

# PART II — practitioner-proof methods (scraped 2026-11-01, sources below)

## P1 — The production numbers (Anthropic Engineering: "How we built our multi-agent research system", Jun 2025)
- Multi-agent beat the best single agent by **90.2%** on their research eval -
  for BREADTH-first, parallelizable, multi-tool tasks.
- **Token usage alone explains 80% of the variance** in BrowseComp results;
  multi-agent = ~15x chat tokens. Swarms are basically a way to buy tokens:
  only worth it where task value pays for 15x.
- Proven practices: (1) teach the orchestrator to DELEGATE - each subtask needs
  objective + output format + tool guidance + boundaries (vague tasks duplicate
  work); (2) SCALING RULES in prompts (1 agent/3-10 calls for facts; 10+ subagents
  only for complex); (3) subagents write ARTIFACTS to a filesystem and return
  lightweight references - kills the game-of-telephone; (4) end-state evaluation
  over turn-by-turn; (5) start wide, narrow later; (6) agents repair their own
  tool descriptions (40% task-time cut); (7) resume-from-checkpoint durability,
  rainbow deployments, LLM-as-judge + human edge-case hunting.

## P2 — The counterpoint (Cognition: "Don't Build Multi-Agents", Walden Yan)
- Two principles worth treating as LAW: (P1) SHARE FULL TRACES, not messages;
  (P2) actions carry implicit decisions - conflicting unstated decisions poison
  merged work. Rule out architectures that violate them by default.
- Their verdict: in 2025+, dispersed multi-agent collaboration is FRAGILE; the
  safe zones are (a) single-threaded linear agents with a compressor model, and
  (b) subagents that only ANSWER QUESTIONS (investigation), never parallel edits.
  Claude Code's subagents were deliberately built that way.
- RECONCILIATION for this family: the swarm is safest exactly where it already
  lives - independent READ-ONLY discovery (lanes/ghosts) whose artifacts merge
  through digest gates. Coordination EDITS (debates writing shared state) are
  the fragile zone Cognition warns about - keep them minimal and reviewed.

## P3 — Verifiable tasks are where teams pay (Self-Organizing Agent Teams, arXiv:2609.22682)
Fixed teams that LEARN teamwork strategies from ~15-25 problems reached 66.7% vs
48.8% (strongest member). The strongest predictor of swarm benefit across eight
benchmarks: demonstrability (rho=0.90) - swarms help when correct reasoning is
RECOGNIZABLE once produced. Bug-finding (compile passes/fails) is the most
demonstrable lane this family has - the literature independently says so.

## P4 — Organization: pooled + sequential interdependence (ORCH, arXiv:2609.11737)
Parallel-pool what can run concurrently; sequence what has prerequisites.
+64%/+74% over four prior frameworks on 25 missions. Wave-discovery then
README-harvest is already this shape - keep the phases explicit.

## P5 — Scaling principles (arXiv:2607.27942): simplicity, elastic feedback,
sequential workflows w/ optional loops, SUMMARY-BASED communication; scaling pays
only above a model-capability threshold; performance PEAKS at intermediate
complexity then degrades. Confirms D1 for an 8B-brain box.

## P6 — Heterogeneity is the ingredient (arXiv:2607.07729)
Heterogeneous model teams: 0.64 vs 0.54 step accuracy, 2.3x over homogeneous.
The family's mixed engines (r1 planner + qwen3-8b chat + coder models) are
validated; replicating one model everywhere would NOT be.

## P7 — Governed fleet identity (Fusion-MoA, arXiv:2609.26080)
Expose heterogeneous cells as ONE service: a versioned Profile controls
membership + evidence admission; read-only Analysts; ONE Executor holds all
tool authority; promote/rollback without breaking the API. The family already
has this SHAPE (shards=analysts, chat=executor, selector=profile) - adopt the
versioned-membership + evidence-admission discipline.

## P8 — Learner-free foraging physics (arXiv:2610.25113 + arXiv:2610.24865)
A swarm with NO learner reaches the explore-exploit equilibrium via Levy flights
+ threshold-cascade recruitment that self-limits as patches crowd: up to **7.6x
solitary harvest when resources are sparse and clustered - and nothing when
search is easy**. GitHub-land is sparse-and-clustered: recruitment-to-crowding
coupling (mine-rich lane draws neighbors until dedup saturates, then disperse)
is the physics of the family's lanes; RL buys precision, not allocation.

## P9 — Agreement is not the goal (arXiv:2609.23310)
Communication can raise agreement while LOWERING accuracy (72.6% -> 91.2% or
-> 65.9% by message orientation alone). Never measure swarm health by consensus
alone - measure by task-verified output. Reinforces D2/D4/D9.

## P10 — Summary beats history as records grow (AgentCue, arXiv:2610.16621)
At scale, full execution histories explode reading cost and degrade
self-organization; compact statistical summaries restore it. Validates the
family's pheromone shares and the D5 synthesis rule.

Sources: export.arxiv.org API (2 queries, 14 papers), anthropic.com/engineering
(production post), cognition.ai/blog (counterpoint), hn.algolia.com (practitioner
signals). All scraped 2026-11-01 keyless; Semantic Scholar still 429 (skipped).