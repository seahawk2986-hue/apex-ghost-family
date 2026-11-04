# THE SWARM PROTOCOL (apex-swarm/1)

**An open standard for self-organized LLM capacity. Anyone, anywhere can
run a node with 2 files and their own free keys. $0, stdlib-only.**

*The sourcing: this session's receipted canon — self-consistency,
Wang et al. (arXiv:2203.11171); debate (arXiv:1805.00899); the Vickrey
auction (RoleMarket); the MCP registry (official) as the join-door
model. Composition + the honesty laws are the fleet's own.*

## The node door (2 endpoints, JSON)

| Endpoint | Request | Response |
|---|---|---|
| `GET /health` | — | `{"ok": true, "region": "...", "capacity_left": n, "protocol": "apex-swarm/1"}` |
| `POST /ask` | `{"prompt", "max_tokens", "purpose"}` | `{"reply": "..."}` (empty reply = the node stays silent, refused) |

## The five laws (enforced in SwarmWide.py + every node kit)

1. **Opt-in only** — a node exists in the registry after its OWNER asks
   (a GitHub issue, the template). Nobody is scanned, pulled, or pooled
   without consent.
2. **Keys stay home** — a node's API keys live on ITS box only. The
   swarm never pools, shares, or ships credentials.
3. **Caps are theirs** — the registry carries each node's `daily_cap`
   and the fleet will never route more onto it than stated. (The cap is
   enforced TWICE: on the fleet side and in the node kit itself.)
4. **Private never routes wide** — purposes tagged private (chat,
   founder memory, the red-team's delivery) are refused by swarm-wide
   routing, by construction and asserted by the certifier.
5. **Instant revocation** — a node stops serving (or zeroes its cap) and
   the next hourly ping drops it back to candidate silently.

## The join path today

```
1. python Scripts/SwarmNodeServer.py        (your box; port 8082)
2. open the repo's issue template "ADD MY NODE"
3. the next ping-hour verifies you (a health ping + one real ask,
   delivered AT YOUR OWN DOOR - the pre-v1.1 path routed candidate
   verification through the verified-only rotation, which could never
   seed its first node; that deadlock was found by the certifier's
   live-fire and fixed by measuring at the candidate's door)
4. your node enters the worldwide rotation until you withdraw
```

## The quorum guarantee (the swarm's S+ shape)

Important answers ship **quorum-backed**: 3 granite-diverse seats (no
two share weights) answer; agreement is measured SEMANTICALLY first
(an embedded cosine - lexical difflib structurally diverged across
different-weight seats) with the lexical fallback when the embedder
sleeps; the receipt names which instrument it used (`sims_metric`). A
divergent vote escalates to a judge rather than shipping an unverified
claim. Every receipt (seats, similarity, metric, verdict) lands in the
fleet's public repo.

## The certifier

`Scripts/SwarmCert.py` udderly grades the swarm against ITS OWN
published grid (the 8 checks; the S+ gate requires delivery n>=50 @
>=95%, quorum n>=30 @ >=70% consensus, 7 clean nightly certs). The grade
may only rise on receipts. No exceptions, including for us.
