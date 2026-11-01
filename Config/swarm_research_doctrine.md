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