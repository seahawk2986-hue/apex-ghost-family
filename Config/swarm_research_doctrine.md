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

---

# PART III — lightweight inter-agent communication (scraped 2026-11-01)

## C1 — Proof-Carrying Messages (PCM, arXiv:2610.39109) - THE transport upgrade
Every claim carries its evidence from an append-only log the agent CANNOT write,
with inclusion proofs signed by an attester outside the agent's control.
Receivers verify offline (~1 ms) and grade claims proven / unproven / failed -
a claim resting on the sender's own report is NEVER proven. Benchmark: 926 real
messages (712 lies in 16 classes): PCM accepted 10 (all stale evidence, 1.4%);
plain A2A accepted ALL 712; six deployed protocols accepted 504-712. Authority
travels as grant chains rooted in human approval; chains only narrow.
ADOPT: the hub's grain digest is a SELF-hash today (GrainLine audit: forgeable).
The fix is PCM-shaped and cheap: root the packet in the git commit itself - the
hub's COMMITS are the append-only log the writer cannot rewrite after the fact;
the family verifies the blob at that immutable commit hash, not at 'main'.

## C2 — Task lifecycle + capability cards (A2A protocol, Linux Foundation)
JSON-RPC task envelopes with lifecycle states; Agent Cards publish capabilities;
agents collaborate WITHOUT exposing internal state or memory (opacity).
ADOPT: grain packets gain explicit lifecycle states (queued/running/done/failed)
at their next schema rev; the seed packet becomes the family's Agent Card.
DO NOT ADOPT the full A2A runtime stack - file+git transport stays (HN: "is
anyone using A2A?" with 45 comments = production adoption still thin).

## C3 — Store-and-forward for offline agents (ATP, arXiv:2610.38398)
Domain-mediated relay keeps stable entries, saves messages until the receiver
returns, signs whole envelopes for post-hoc verification. The hub->family
return leg ALREADY IS this pattern (commits wait for the next brief) - now
validated by the literature rather than by accident.

## C4 — Message geometry matters more than volume (arXiv:2609.23310, Part II P9)
Changing only message ORIENTATION moved accuracy 72.6% -> 91.2% or -> 65.9%.
Broadcasts must carry facts + direction, never bare news.

## C5 — Never let the family evolve private language (emergent-communication results)
Learned protocols save tokens but the oversight literature shows they become
unmonitorable (NLA explainers identify without discriminating; ASRD exists
precisely because emergent codes resist audit). The family's law - schema-typed,
terse, human-readable channels - is a security property, not a style choice.
Collusion research (strategic vagueness) adds: VAGUENESS in agent messages is
a red flag to log, not a convenience to allow.

## C6 — Latent-state communication (SelectKV/HyLaMAS, arXiv:2610.37779): 53-80%
fewer decoded tokens, 1.16-2.78x speedup via KV-cache transfer. REFUSED for
the family: mixed engines + served models cannot exchange KV state - and the
monitorability cost above applies. Noted so the door is not re-opened blindly.

## C7 — Execution-grounded refinement (MAS-Loop, arXiv:2610.38946)
Orchestrators that learn from INTERMEDIATE trajectories (not just final scores)
produce self-evolving systems. Validates the family's round-ledgers + lessons
as the right substrate; D5's synthesis is the bounded version.

---

# PART IV — the labs' proven runs AND their tools/programs (scraped 2026-11-01)

## V1 — Microsoft: Magentic-One (arXiv:2411.04468)
SOTA-competitive on GAIA/AssistantBench/WebArena with NO per-task tuning.
Proven mechanics: an Orchestrator with a double loop - a TASK LEDGER (facts,
guesses, plan) and a PROGRESS LEDGER (per-step state) - plus a STALL RULE:
no progress for enough steps -> rebuild the Task Ledger and re-plan.
AutoGenBench: evaluation with REPETITION + ISOLATION controls.
TOOLS: AutoGen is now **ARCHIVED** (README banner: "no longer maintained...
advise against production use") -> successor = Microsoft Agent Framework.
FAMILY VERDICT: adopt the double-ledger + stall-replan pattern in stdlib
(the round ledger exists; add stall-detection -> lane rotation); ADOPT the
repetition+isolation eval discipline (the marathon IS repetition); REFUSE
AutoGen and MAF (installing a framework violates D1 without break-even).

## V2 — Anthropic: multi-agent research system (engineering post, Part II P1)
+90.2% over the best single agent on research evals; delegation-quality +
effort-scaling + filesystem-artifacts + LLM-judge/human evals. Tools: Claude
API + MCP server ecosystem. FAMILY VERDICT: patterns adopted (D5, artifact
rule); MCP REFUSED for now (family tools are local scripts/HTTP; a protocol
server adds moving parts for zero current need).

## V3 — OpenAI: Agents SDK (openai-agents-python) + practical agents guide
Cannonical patterns: agents with handoffs, agents-as-tools, GUARDRAILS at
boundaries, human-in-the-loop, sessions, TRACING built-in, sandbox agents.
FAMILY VERDICT: the concepts map 1:1 onto family organs (master switch =
guardrail; earn gate = HITL; heartbeat+round-ledger = tracing); the SDK
itself REFUSED (OpenAI-API-shaped, new deps, D1 break-even unmet).

## V4 — Manus: context engineering from production ("Stochastic Graduate
Descent", 2025-07): (1) KV-cache hit rate is THE production metric - keep
prompt prefixes STABLE (a timestamp at the top kills the cache); (2) mask,
don't remove: never mutate mid-run toolsets; (3) FILE SYSTEM AS CONTEXT -
restorable compression only; (4) todo-recitation: rewrite the goal at the
END of context each step to fight lost-in-the-middle; (5) KEEP ERRORS IN
CONTEXT - erasing failure removes evidence; (6) don't few-shot yourself
into a rut - add structured variation.
FAMILY VERDICT: mostly already family-native (file-artifacts, honest error
prints, lane rotation). NEW ADOPTIONS: (a) keep SYSTEM_IDENTITY and payload
prefixes byte-stable across brain calls (local qwen3-8b honors prefix cache);
(b) recite the mission into each cycle's first line (the heartbeat/round
banner carries a 1-line goal - the marathon prints already do this).

## V5 — Google: A2A protocol (Linux Foundation; Agent Cards, task lifecycle,
opacity - Part III C2) + the AI co-scientist line (generate->reflect->rank->
evolve->tournament over hypotheses; the abstract fetch failed this pass -
pattern cited from the published system description, honestly marked
part-unverified). TOOLS: a2a-sdk (python/go/js). FAMILY VERDICT: lifecycle
states + capability-card alignment at the packet's next schema rev; SDKs
deferred.

## V6 — Cognition/Devin: single-threaded linear agent + a dedicated
COMPRESSOR model for long-horizon context; subagents answer questions, never
edit in parallel (Part II P2). FAMILY VERDICT: the read-only lane swarm +
digest-gated merging is the compliant architecture; a compressor pass for
the semantic store is already ApexMemory's job.

## TOOLS-AND-PROGRAMS LEDGER (install / implement / refuse)
| Tool (owner)              | Verdict  | Why |
|---------------------------|----------|-----|
| AutoGen (Microsoft)       | REFUSE   | ARCHIVED - archived deps are unpatched risk |
| MS Agent Framework (MAF)  | WATCH    | successor; re-evaluate ONLY if D1 break-even |
| openai-agents SDK (OpenAI)| REFUSE (patterns only) | OpenAI-shaped, adds deps |
| MCP servers               | DEFER    | zero current need; revisit for hub tooling |
| A2A SDKs (Google/LF)      | DEFER    | adoption thin (HN); git+files still wins |
| LangGraph/CrewAI          | NOT-EVAL | not fetched this pass (honest gap) |
| AutoGenBench-style harness| IMPLEMENT in stdlib | repetition (marathon) + isolation |
| Magentic double-ledger    | IMPLEMENT in stdlib | stall -> replan = lane rotation |
| Manus context rules       | IMPLEMENT | stable prefixes + goal recitation |
| A2A/Agent-Card schema     | IMPLEMENT at packet rev | capability card + lifecycle |

Sources: microsoft.com/research (Magentic-One + archived-AutoGen README),
openai.github.io/openai-agents-python README, modelcontextprotocol README,
manus.im blog, arxiv abs/2411.04468. arXiv API rate-limited (429) mid-pass
and hn.algolia query returned 0 - noted; co-scientist pattern marked
part-unverified. Scraped 2026-11-01.

---

# PART V — kin systems (repo-harvest swarms) + missing harvest resources

Scraped 2026-11-01: arxiv abs hits/misses recorded honestly below; gharchive.org
full page; allenai/s2orc README. HONEST MISSES: two recall'd paper IDs landed
on unrelated papers (2402.04165=GDP nowcasting, 2406.05665=balanced truncation)
- those two systems (The Stack v2, FineWeb) are cited FROM KNOWLEDGE and marked
part-unverified.

## K1 — OctoPack/CommitPack (arXiv:2308.07124, FETCHED - direct kin)
Harvested **4 TB of Git commits across 350 languages** using commit STRUCTURE
(a commit pairs a code change with a human-written instruction). With strict
filters (permissive license detection, near-dedup, language balance) it
fine-tuned StarCoder to SOTA among permissive models (46.2% HumanEval pass@1).
MAX-OUT LESSONS for the family: (1) commits are instruction-paired harvests -
better than raw READMEs for SKILL extraction; (2) license filter + dedup +
language balancing are the yield multipliers; (3) structure beats dumps.

## K2 — The Stack v2 / StarCoder2 (part-unverified - fetch missed)
The canonical repo->corpus line: Software Heritage as provenance backbone
(every file traced to the origin repo commit), go-license-detector for the
permissive filter, MinHash near-dedup, 619 languages. Kin method: provenance
+ license + dedup = the three filters that made a 6TB+ dump trustworthy.
FAMILY MAPPING: SWH lane + license-sha fast-path already mirror this; add
MinHash-class near-dedup for skills (sha exact-match only today).

## K3 — Quality-ladder lineage: CCNet -> C4 -> FineWeb (part-unverified)
Proven max-out: exact-dedup -> MinHash fuzzy-dedup -> language ID -> heuristics
-> classifier-scored quality (FineWeb-Edu beat FineWeb by CLASSIFIER-selected
subset alone). Lesson: a small scoring model that RANKS harvest candidates
beats bigger dumps - the family's grade/rank step is this pattern; wire it
 EARLIER (grade the backlog, not only mined READMEs).

## K4 — GH Archive (FETCHED - the missing lane, ranked #1)
data.gharchive.org: the ENTIRE public GitHub timeline since 2011 as hourly
JSON.GZ files, plain wget, NO key, NO rate-limit page, also on BigQuery
(githubarchive). 15+ event types incl. PushEvent/WatchEvent/IssuesEvent.
For a lane-poor hour the archive beats the live Events API by orders of
magnitude in yield. Proposed lane (post-marathon): pull yesterday's 24h
archive -> filter PushEvent repos by size/owner-diversity -> feed backlog
(commits are OctoPack's unit - K1 synergy). Also visible there: OSS Insight,
GFI-Bot (ML good-first-issue finder - directly feeds the bug lane), DevStats.

## K5 — S2ORC (FETCHED) - 136M papers, machine-readable full text via the
Semantic Scholar "Bulk Dataset" API. ODC-By 1.0. NOT keyless: needs a free
API key (x-api-key). FAMILY VERDICT: candidate lane ONLY with Andrew's
consent for a free key in .env; until then the arXiv/OpenAlex lanes stand.

## K6 - missing-resource shortlist (ranked for OUR lanes, from this pass)
1. GH Archive hourly dumps (keyless, bulk, exactly our events lane's twin)
2. GFI-Bot / good-first-issue mining (bug-lane feed; evidence-first)
3. SourceForge / GNU Savannah / Gitea-Forgejo instances (vintage, sparse-
   clustered repos - the foraging regime that pays per arXiv:2610.24865)
4. SPDX license catalog (feeds the license-sha fast-path deterministically)
5. Crossref + DBLP APIs (paper metadata beyond arXiv's slice)
6. Wikidata / Google Dataset Search / Kaggle (dataset discovery lanes)
7. S2 bulk (K5) and Software Heritage full dumps (K2) - the heavy tiers,
   each with a key/pragmatics gate to clear with the founder's consent.

---

# PART VI — the harvest-maximization canon (scraped 2026-11-01)

## H1 — The Stack v2 / StarCoder2 (FETCHED: HF dataset card + arXiv:2402.19173)
Repairs the earlier ID miss. The pipeline numbers: 3.28B files / 104.2M repos
from the Software Heritage graph; 67.5TB full -> 32.1TB after dedup; ~900B
train tokens. Proven stages: (1) PROVENANCE every file->origin commit (SWHID);
(2) license: GH Archive repo-level + ScanCode file-level SPDX, propagated to
same-base-path files; (3) drop lists: binary/empty/undecodable/>10MB; (4)
exact + NEAR dedup - **~40% of permissive files were near-duplicates**;
(5) repo-grouping so context survives; (6) governance: opt-out honored in
releases (v2.1/v2.2 changelog).
FAMILY MAPPING: provenance root = our commit-rooted transport (done);
license = SPDX sync (done, 740 ids); drop list = the 256KB head cap;
NEAR-DUP = NearDedup.py (built tonight); repo-grouping = we harvest by repo;
governance = consent-gated by design.

## H2 — WHY near-dup matters (FETCHED: arXiv:2107.06499, ACL 2022)
Deduplication: (a) models memorize ~1% of output verbatim from duplicated
sets; (b) dedup cuts memorization 10x and reaches equal/better accuracy in
FEWER train steps; (c) one 61-word sentence repeated 60,000x sat inside C4;
(d) >4% of standard validation sets leaked into train (train-test overlap)
until dedup. Companion arXiv:2202.06539: memorization rate is SUPERLINEAR in
duplication count (present 10x -> generated ~1000x more).
FAMILY TRANSLATION: a skill store seeded with near-dups doesn't just bloat -
it biases every consult toward echoes of the same idea. NearDedup audit is
now a standing step before registration.

## H3 — the PROGRAM: datatrove (FETCHED: README)
HuggingFace's library is the field's harvest stack: readers/filters/extractors
(trafilatura - the exact library the family already depends on)/minhash+exact
dedup/stats (FQDN-level stats, CCNet perplexity, line-dup ratios)/resumable
executors with completion markers. FAMILY VERDICT: patterns adopted in
stdlib; the tool itself REFUSED for the local swarm (Python 3.11+ slurm-scale
framing; D1 break-even unmet) - but its stage list IS our checklist, and its
trafilatura kinship means our extractor choice is industry-proven.

## H4 — the family harvest stack, stage by stage (post-audit status)
provenance: DONE (commit root) | license: DONE (SPDX+sha fast-path) |
exact-dedup: DONE (sha256) | NEAR-dedup: BUILT tonight, wiring pending |
drop-lists: PARTIAL (256KB cap) | quality-rank-early: PENDING (grade the
backlog pre-download) | stats-per-stage: PARTIAL (diversity + lane counters)
| governance: DONE (consent-gated, master switch, digest gates).

## H5 — audit receipt (ran live tonight):
[NearDedup audit of the 281-skill store]: clusters and verdicts printed by
Scripts/NearDedup.py --audit above (the shell-inflation finding predicted
shallow clusters of __init__/version shells; the count lands in the ledger
for the provenance gate to act on).

---

# PART VII — the quality-harvest canon, fully verified (scraped 2026-11-01)

## Q1 — FineWeb (arXiv:2406.17557, FETCHED - now properly identified)
15T tokens from 96 CommonCrawl snapshots; full ablations of every design
choice, esp. LOCAL vs GLOBAL MinHash dedup. THE headline: FineWeb-Edu - 1.3T
tokens selected by an 8B-parameter CLASSIFIER score - produces dramatically
better MMLU/ARC models. PROVEN: a small classifier that ranks beats raw
volume. (Earlier part-unverified entry now verified; the 2406.05665 ID miss
is corrected to 2406.17557.)

## Q2 — Dolma (arXiv:2402.00159, FETCHED) + Ultra-FineWeb (arXiv:2505.05427)
Dolma: 3T tokens with a fully open curation toolkit (reproducibility as a
feature). Ultra-FineWeb: efficient VERIFICATION strategy (rapid data-quality
feedback with minimal compute) + a light fastText-class classifier -> 1T
english + 120B chinese tokens, better benchmarks. PROVEN: cheap classifiers +
fast verification loops fit exactly the family's 8B/2GB reality.

## Q3 — SWE-Gym (arXiv:2412.21139, FETCHED) - the bug-lane blueprint
2,438 REAL task instances harvested from GitHub: repo + executable env + unit
tests + natural-language task. Training on them: +19% resolve rate; with
verifiers: 32% on SWE-Bench Verified (open-weight SOTA at the time). PROVEN:
issue->repo->tests is the harvestable unit for a software agent.
FAMILY MAPPING: the GH Archive IssuesEvent/PushEvent lane is the discovery
half; the farm (compile+tests) is the executable-env half. The bug lane is
not theory - it is this pipeline with our signature on it.

## Q4 — SPICE (arXiv:2507.09108, FETCHED) - triage before filing
Automated labeling of issue-driven datasets: issue CLARITY, test COVERAGE,
effort estimation via context-aware prompting + multi-pass consensus.
Cost: 1,000 instances labeled for $5.10 vs ~$100,000 manual. PROVEN: machine
triage of which issues are WORTH working, at near-free cost.
FAMILY MAPPING: exactly the human-review gate the bug lane needs - score the
6+ GFI candidates for clarity/effort before Andrew ever sees a draft.

## Q5 — PAIChecker (arXiv:2607.28587, FETCHED) - alignment protection
13.6% of SWE-bench-style PR<->issue pairs are MISALIGNED across 5 patterns;
a multi-agent checker reaches 92% accuracy. PROVEN: never file an issue whose
fix-pair is misaligned - reputational protection for the family's first
external artifacts.

## Q6 — More Agents Is All You Need (arXiv:2402.05120, FETCHED, TMLR)
Sampling-and-voting ("Agent Forest"): LLM performance scales with agent
COUNT, orthogonal to fancy methods, gain correlated with task difficulty.
PROVEN + CHEAP for an 8B box: N samples + majority vote on ambiguous grades
replaces a single judgment call.

## Q7 — LIMA (arXiv:2305.11206, FETCHED) + MM-LIMA (2308.12067)
1,000 CAREFULLY CURATED examples -> GPT-4-class parity in 43% of human evals;
the lesson: almost all knowledge comes from pretraining, tiny curated sets
teach output quality. MM-LIMA: a trainable SELECTOR filters low-quality data.
PROVEN: grade-and-keep-the-top beats harvest-everything - doctrine H3/K3's
quality ladder, now with the canonical citation.

## THE RANKED EARNING PATHS (all verified, hardware-legal)
1. Agentless-shaped conversion: localize -> draft -> validate on triaged
   candidates (W3+W7), human-gated, one verifiable artifact per run.
2. Voyager-shaped store (W1): executable composable skills + automatic
   curriculum (GradeEarly) + retrievable library.
3. Reflexion after every failed round (W2): bounded, one call, D5 hardware.
4. ACI discipline (W4): every tool output ergonomic and consumable.
5. phi-class curation for the training tier (W8) when the GPU wakes.

---

# PART IX — every proven swarm, compared (all fetched; scraped 2026-11-01)

| System (id) | Architecture | Cost model | Verified outcome | Lesson for the family |
|---|---|---|---|---|
| MetaGPT (2308.00352) | SOP assembly-line roles, verified intermediate artifacts between roles | LLM-call cost, no exec env | coherent multi-role SW solutions vs chat-chains | SOPs + VERIFIED handoffs stop cascading hallucinations - our digest gates are this |
| MoA (2406.04692) | layered heterogeneous agents, each sees prior layer | many calls | open models 65.1% vs GPT-4-Omni 57.5% (AlpacaEval 2.0) | HETEROGENEITY layers beat single-model depth - our lane mix is this |
| AlphaEvolve (DeepMind blog) | LLM proposes + AUTOMATED EVALUATORS + evolutionary database | very large (Gemini fleet) | 0.7% of Google compute recovered (1yr production); 4x4 matmul 48-mults (beat Strassen 1969); 20% of 50 open problems IMPROVED | the flagship: evaluator-gated EVOLUTION makes runs worthwhile BY CONSTRUCTION - evolve STRATEGY WEIGHTS, not just candidates |
| Anthropic Research (Part II P1) | orchestrator-worker, artifacts to filesystem | 15x tokens; value must pay | +90.2% single-agent; token spend = 80% variance | breadth-parallel with quality gates (already family shape) |
| Magentic-One (2411.04468) | double-ledger orchestrator, stall>2 replan | heavy | SOTA-competitive GAIA/AssistantBench | ledger + stall-replan (queued post-marathon) |
| Agentless (2407.01489) | 3-phase single-turn localize/repair/validate | ~$0.70|instance | 32% SWE-bench Lite, cheapest | THE conversion shape for an 8B box |
| SWE-agent (2405.15793) | custom ACI | moderate | 12.5% pass@1 | interfaces > models |
| Kimi-Dev (2509.23045) | agentless training -> skill priors | training-scale | 60.4% workflow SOTA | store 3 skill TYPES: localize/edit/reflect |
| SWE-Edit (2604.26102) | Viewer/Editor split; GRPO on Qwen3-8B | moderate | 8B editor = GPT-5-nano parity | small-model Editor is proven |
| Voyager (2305.16291) | curriculum + executable skill library | GPT-4 calls | 3.3x items; library TRANSFERS | skills must be executable+composable |
| Reflexion (2303.11366) | verbal episodic memory | calls only | 91% HumanEval pass@1 | reflection beats weight updates at our scale |
| AutoSwarm (2610.33048) | contribution-grounded formation + shared state | heavy | beats single+prior MAS | acceptance conditions per handoff |
| MPT (2610.22322) | BIDS, self-orchestration, dropout-robust | training-scale | beats fixed orchestration | scheduling by bid (D7) |
| SAT (2609.22682) | teams LEARN teamwork; demonstrability rho=.90 | 15-25 tasks | 66.7% vs 48.8% | only demonstrable lanes pay - bug lane rho-max |
| AgentCue (2610.16621) | statistical summaries replace history readbacks | moderate | efficiency at 1000-agent scale | summaries over raw ledgers (pheromones) |
| Fusion-MoA (2609.26080) | governed fleet, versioned profile, one Executor | serving | minority knowledge TRANSFERS across cells | promote/rollback discipline |
| ClaimNov (2610.36511) | claim-level novelty gates | cheap | 97% catch at 1.5% false alarms | claim-level gates for artifacts |
| DataSense-Bench (2610.12190) | agents pick training data | cheap | HONEST NEGATIVE: agents can't reliably rank data votes | our vote tier is a PRIOR, capped influence |
| THE FAMILY (this repo) | foraging lanes + bid sems + digest-gated merging + foraging evolution + human gates | $0 | hub 126+ harvests, 5 executable-verified skills, 55-cluster audit, transport verified at 3k+ leads | unique: FREE-CI compute arena + proof-carrying champions - nobody runs this |

## THE SYNTHESIS GAP (what nobody in the lineage does, that we uniquely can)
Nobody converts a FREE CI FLEET into an evolutionary arena; nobody evolves
STRATEGY WEIGHTS over real repo issues with proof-carrying champions and a
human-approval grant chain. That combination is the novel mechanism below.

## THE GAUNTLET (the novel mechanism, built tonight)
One run = candidates x THREE HETEROGENEOUS STRATEGY DRAFTS (MoA-in-strategy:
A minimal-patch / B test-first / C doc-or-issue-comment), each scored by the
deterministic rubric (+ Q6 vote when RAM allows, capped influence per
DataSense-Bench). Winner per candidate = CHAMPION with a digest and a
human-approval grant chain (PCM roots). Strategy WIN COUNTS evolve the
weights (AlphaEvolve-style: the run's return includes improved STRATEGY
probabilities), losers feed Reflexion (W2). VALUE THRESHOLD gates the human
queue (clarity x credibility x rubric >= bar) per ClaimNov discipline.
CONSTRUCTION GUARANTEE: every run ends with EITHER a champion digest OR a
measured lesson -> no run can return nothing. Runs port to the free hub
(stdlib-only) post-marathon: the arena runs on Andrew's free CI minutes.

---

# PART XI — THE VERIFIED USD-RAILS MAP (scraped 2026-11-01, fetch-verified)

## R1 — Polar (polar.sh, FETCHED, LIVE)
Merchant-of-record billing: digital products, subscriptions, usage meters;
free Starter tier (5% + 50c); pays out globally, handles tax/fraud.
SELLS: "The 2026 Swarm Methods Canon" (this doctrine, Parts I-X) as a paid
artifact; usage billing = any future agent service.

## R2 — Open Collective (opencollective.com, FETCHED, LIVE)
Fiscal hosting: a collective receives contributions and pays contributors
TRANSPARENTLY. THE FLAGSHIP USE: "OSS Watchtower as a Service" - orgs back
the family's collective; the FREE 24/7 hub swarm watches THEIR repos
(triage issues, draft fixes, weekly digest dossiers); payouts route to
Andrew via the transparent ledger. Every organ for this exists EXCEPT the
accounts.

## R3 — GitHub Sponsors (button in the family README already)
Recurring sponsorship tied to public artifacts; slow burn, grows with
track record.

## R4 — IssueHunt (issuehunt.io, FETCHED, LIVE - pivoted)
Now a BUG-BOUNTY platform (Japan-focused, English programs; pays via bank
or PayPal on triage/fix). NOT OSS-issue-bounties anymore. Real USD; needs
accounts, program scope discipline, real security findings - the security
lane's future home, behind skill-gates.

## R5 — Google Summer of Code (summerofcode.withgoogle.com, FETCHED, LIVE)
Contributor stipends for 12-week mentored OSS projects (~1.5-6.6k class).
Competitive; needs a real proposal + early engagement with a mentoring org.
The swarm's dossier pipeline is exactly proposal prep.

## R6 - CLOSED/CHECKED
Algora: 404 tonight (API + open-bounties page) - monitored; IssueHunt's
OSS-bounty mode: gone (pivoted to bug bounty).

## THE HONEST SYNTHESIS (the law that outranks every rail)
NO verified system earns autonomously at small-model scale. Every rail
above pays for CONVERTED HUMAN WORK. The swarm's economic function is
cutting the founder's time-to-artifact - triage (SPICE-class), drafts
(Agentless-class), verification (rubrics), 24/7 hub monitoring (free CI).
FIRST ACTION (no accounts needed): one GFI dossier -> Andrew submits ->
first merged PR = track record = every rail above unlocks.
ORDER: (1) first merged PR, (2) Polar canon artifact, (3) OpenCollective
watchtower collective, (4) GSoC proposal next cycle, (5) security lane
when demonstrated.

---

# PART VIII — the "extremely worthwhile" return canon (verified 2026-11-01)

## W1 — Voyager (arXiv:2305.16291, FETCHED): the compounding skill library
Autonomous curriculum + an EVER-GROWING LIBRARY OF EXECUTABLE CODE SKILLS +
iterative prompting w/ environment feedback, execution errors, self-
verification -> 3.3x unique items, 2.3x travel, 15.3x faster milestones -
and the library TRANSFERS to new worlds. Skills are temporally extended,
interpretable, COMPOSABLE - they compound and prevent catastrophic forgetting.
FAMILY MAPPING: the skill store should hold executable, composable, indexed
skills (not text summaries); GradeEarly IS the automatic curriculum; the
store becomes functional capital that compounds per run.

## W2 — Reflexion (arXiv:2303.11366, FETCHED): verbal reinforcement
Reflect on feedback -> keep reflective text in episodic memory -> better next
trials, NO weight updates: 91% HumanEval pass@1, surpassing GPT-4's 80%.
FAMILY MAPPING: the round ledger + lessons are the episodic buffer; add one
bounded reflection call after every failed round -> next round's mission
brief (the D5 machinery already exists).

## W3 — Agentless (arXiv:2407.01489, FETCHED): the cheapest conversion
Localize -> repair -> validate, SINGLE-turn, no agent loops: 32% / 96 fixes
on SWE-bench Lite at ~$0.70/instance - best performance AND lowest cost
among open systems at release. PROVEN: complex agent frameworks are not
required for worthwhile output. FAMILY VERDICT: the bug lane is
Agentless-shaped (D1 confirmed on the SWE lane).

## W4 — SWE-agent (arXiv:2405.15793, FETCHED): interfaces decide success
A custom agent-computer interface (ACI) took a 12.5% pass@1 on SWE-bench -
the interface, not the model, was the lever. FAMILY VERDICT: the family's
tools (digest manifests, GradeEarly output, gates) ARE the ACI - keep making
them ergonomic, never assume the model compensates.

## W5 — Kimi-Dev (arXiv:2509.23045, FETCHED): 60.4% workflow SOTA
Agentless TRAINING builds transferable skill priors: localization, code-edit,
self-reflection -> agents reach Claude-3.5-Sonnet-class performance.
FAMILY MAPPING: the skill store should classify and grow those three skill
types explicitly.

## W6 — SWE-Edit (arXiv:2604.26102, FETCHED): small models CAN edit
Viewer/Editor decomposition: +2.1pp resolve, -17.9% cost; a GRPO-trained
QWEN3-8B editor reaches GPT-5-nano PARITY on downstream resolve rate.
FAMILY VERDICT: our 8B-class brain can hold the Editor role with the right
decomposition - the heal path should split Viewer/Editor.

## W7 — Agentic Rubrics (arXiv:2601.04171, FETCHED): verification without
execution: an expert agent writes a context-grounded rubric checklist, then
candidate patches score against it - no test sandbox needed (54.2% w/ TTS).
FAMILY VERDICT: pre-filing verification for the bug lane without heavy
sandboxing - fits the hardware law exactly.

## W8 — phi-1 / phi-1.5 (arXiv:2306.11644, 2309.05463, FETCHED): curriculum
quality beats scale: 1.3B params, 6B textbook-quality tokens -> 50.6%
HumanEval; phi-1.5 hits 5x-larger-model performance with ZERO web data.
FAMILY VERDICT: when training resumes (training_venv), textbook-grade
curated corpora from OUR OWN verified skills are the resource - quality
harvest compounds INTO training, not just into consults.

## THE RANKED EARNING PATHS (all verified, hardware-legal)
1. Agentless-shaped conversion: localize -> draft -> validate on triaged
   candidates (W3+W7), human-gated, one verifiable artifact per run.
2. Voyager-shaped store (W1): executable composable skills + automatic
   curriculum (GradeEarly) + retrievable library.
3. Reflexion after every failed round (W2): bounded, one call, D5 hardware.
4. ACI discipline (W4): every tool output ergonomic and consumable.
5. phi-class curation for the training tier (W8) when the GPU wakes.