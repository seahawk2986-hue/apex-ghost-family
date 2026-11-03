"""SourcingMap - THE CONNECT PASS (2026-11-03; the founder's question:
'were they documents sourced proven ways to help the swarm become
S+?' - and the honest answer was NO, not automatically. Provenance
[the org's own page, fetched live] and usefulness [moves an S+ gate]
are DIFFERENT claims. This pass makes usefulness measurable:

  every VERIFIED doc -> either
    CONNECTED:   technique + the LIVE organ implementing it + the S+
                 gate it moves (organ existence checked on disk), or
    BACKGROUND:  proven-but-unconnected, named honestly (the corpus
                 carried vision/speech/diffusion papers for company
                 COVERAGE - they do not move the gates, and saying so
                 is the honesty law), or
    UNMAPPED:    a verified doc I forgot to classify - printed LOUDLY
                 (must stay 0 or the map is incomplete, never hidden).

The S+ gates (public in swarm_cert.json s_grid): all-8 checks,
delivery n>=50@95%, quorum n>=30@70%, 7 clean nights (+ spread)."""

import json
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get(
    "APEX_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = os.path.join(ROOT, "Config", "sourcing_ledger.jsonl")
MAP_F = os.path.join(ROOT, "Config", "sourcing_map.json")
STATE_F = os.path.join(ROOT, "Config", "sourcing_connect_state.json")

# the live organs a technique can land in (existence-checked on disk)
ORGANS = {
    "SwarmCert": "Scripts/SwarmCert.py",
    "QuorumSwarm": "Scripts/QuorumSwarm.py",
    "SwarmWide": "Scripts/SwarmWide.py",
    "FreeSwarm": "Scripts/FreeSwarm.py",
    "ChatRedTeam": "Scripts/ChatRedTeam.py",
    "ApexHands": "Scripts/ApexHands.py",
    "ApexMcpServer": "Scripts/ApexMcpServer.py",
    "SourcingDesk": "Scripts/SourcingDesk.py",
    "NodeDesk": "Scripts/NodeDesk.py",
    "DemoDesk": "Scripts/DemoDesk.py",
    "SWARM_PROTOCOL": "SWARM_PROTOCOL.md",
    "RewardLedger": "Config/RewardLedger.json",
    "family-burst.yml": ".github/workflows/family-burst.yml",
}

GATES = ["all-8", "delivery-n50", "quorum-n30", "7-nights", "spread"]

SEAT = ("open-seat lineage (the pool serves this family's weights)",
        "FreeSwarm", "delivery-n50")
BG = lambda note: (None, None, note)

DOCMAP = {
    # ---- OpenAI ----
    "2303.08774": ("eval-suite discipline (capability probes, not vibes)",
                   "SwarmCert", "all-8"),
    "2005.14165": ("few-shot prompting = zero-training seat lanes",
                   "FreeSwarm", "delivery-n50"),
    "2203.02155": ("instruction-following IS the delivery probe",
                   "SwarmCert", "delivery-n50"),
    "2001.08361": ("compute-optimal seat choice under the $0 law",
                   "FreeSwarm", "all-8"),
    "2107.03374": ("code-seat lineage for the local judge",
                   "FreeSwarm", "quorum-n30"),
    "2112.09332": ("answers carry citations (receipt-first sourcing)",
                   "SourcingDesk", "all-8"),
    "2309.17421": ("disclose-limits-by-name (the system-card honesty)",
                   "SwarmCert", "all-8"),
    "2305.20050": ("process supervision - verify each step, not just ends",
                   "QuorumSwarm", "quorum-n30"),
    "2312.09390": ("weak-to-strong: children supervised by parent gates",
                   "ChatRedTeam", "7-nights"),
    "2210.10760": ("Goodhart guard - dual-metric honesty pair",
                   "QuorumSwarm", "quorum-n30"),
    "1706.03741": ("preference signals land in a reward ledger",
                   "RewardLedger", "7-nights"),
    "2110.14168": ("exact-answer verification probes ('Reply with exactly')",
                   "SwarmCert", "delivery-n50"),
    "2109.07958": ("truthfulness probes = the gate's leak meters",
                   "ChatRedTeam", "all-8"),
    "2103.00020": BG("vision contrastive - no vision organ"),
    "2212.04356": BG("speech - no speech organ"),
    "2204.06125": BG("image generation - no image organ"),
    "2102.12092": BG("image generation - no image organ"),
    "1502.05477": BG("policy-gradient theory; only its spirit informs "
                     "the conservative mutation pacing"),
    # ---- Google DeepMind ----
    "2203.15556": ("compute-optimal economics of the seat pool",
                   "FreeSwarm", "all-8"),
    "2312.11805": ("multi-facet eval suites (8 checks, one verdict)",
                   "SwarmCert", "all-8"),
    "1712.01815": ("the self-play improvement loop (gen -> gate -> gen)",
                   "ChatRedTeam", "7-nights"),
    "2203.07814": ("massive-sample then filter - divergent->judge",
                   "QuorumSwarm", "quorum-n30"),
    "2403.08295": SEAT,
    "2408.00118": SEAT,
    "2302.01318": ("speculative serving for mesh latency",
                   "SwarmWide", "delivery-n50"),
    "2403.05530": BG("long-context; our asks cap at 4000 chars"),
    "1911.08265": BG("world-model RL - no RL organ"),
    "2112.11446": BG("scaling failure analysis - informational"),
    "2212.12794": BG("weather modeling - no organ"),
    "2301.04104": BG("world-model RL - no organ"),
    "2310.08864": BG("robotics data pooling - no organ"),
    "2206.07682": BG("emergence thresholds - informational"),
    "2204.14198": BG("vision-language - no vision organ"),
    "2205.06175": BG("generalist agent - informational"),
    # ---- Google Research ----
    "2201.11903": ("reasoned single-sentence quorum answers",
                   "QuorumSwarm", "quorum-n30"),
    "2210.03629": ("think-act-observe with step receipts",
                   "ApexHands", "all-8"),
    "2101.03961": ("sparse routing across seats/nodes",
                   "SwarmWide", "delivery-n50"),
    "2211.17192": ("speculative serving for mesh latency",
                   "SwarmWide", "delivery-n50"),
    "1910.10683": BG("text-to-text framing - informational"),
    "2204.02311": BG("scaling emergent abilities - informational"),
    "2305.10403": BG("multilingual benchmarks - no organ"),
    "2404.07143": BG("long-context compression - asks capped"),
    "2010.11929": BG("vision backbone - no vision organ"),
    "2303.03378": BG("embodied VLM - no vision organ"),
    "2305.16264": BG("data-constrained scaling - informational"),
    "2201.08239": BG("dialogue safety - informational"),
    "2302.06675": BG("optimizer discovery - no training organ"),
    # ---- Anthropic ----
    "2212.08073": ("written constitution + self-critique = the judge",
                   "QuorumSwarm", "quorum-n30"),
    "building-effective-agents": ("compose small named organs, not one "
                                  "god-loop", "SWARM_PROTOCOL", "7-nights"),
    "modelcontextprotocol.io": ("the worldwide MCP door",
                                "ApexMcpServer", "spread"),
    "2209.11895": BG("circuit interpretability - no interpretability organ"),
    "scaling-monosemanticity": BG("feature interpretability - no organ"),
    # ---- Meta ----
    "2302.13971": SEAT,
    "2307.09288": SEAT,
    "2407.21783": ("open-seat lineage + post-train eval discipline",
                   "FreeSwarm", "delivery-n50"),
    "2302.04761": ("tool-calling grammar for the MCP tools",
                   "ApexMcpServer", "spread"),
    "2308.12950": ("coder judge-seat lineage", "FreeSwarm", "quorum-n30"),
    "2401.10020": ("self-critique inside the evolution gate",
                   "ChatRedTeam", "7-nights"),
    "2304.02643": BG("segmentation - no vision organ"),
    "2304.07193": BG("vision features - no vision organ"),
    "2205.01068": BG("open logs - informational"),
    "2212.12017": BG("instruction metric suites - informational"),
    "2305.13516": BG("speech - no speech organ"),
    # ---- Microsoft ----
    "2306.11644": ("data-quality over scale = the verified-only corpus law",
                   "SourcingDesk", "all-8"),
    "2309.05463": ("synthetic-textbook seats", "FreeSwarm", "delivery-n50"),
    "2311.11045": ("explanation-tuned judging", "QuorumSwarm", "quorum-n30"),
    "2303.12712": ("capability probing before claiming capability",
                   "SwarmCert", "all-8"),
    "2308.08155": ("multi-agent orchestration cadence on runners",
                   "family-burst.yml", "7-nights"),
    "2404.16130": ("verdicts carry their evidence graph",
                   "DemoDesk", "spread"),
    "2106.09685": BG("parameter-efficient tuning - no training organ"),
    "2304.08485": BG("vision instruction tuning - no vision organ"),
    # ---- NVIDIA / Mistral / xAI ----
    "2310.06825": SEAT,
    "2401.04088": ("sparse MoE routing across the width",
                   "SwarmWide", "delivery-n50"),
    "mistral.ai/news": ("the seat-lane announcements feed the pool",
                        "FreeSwarm", "delivery-n50"),
    "2406.11704": BG("synthetic data lineage - no training organ"),
    "2411.13676": BG("hybrid architecture - no local inference organ"),
    "developer.nvidia.com/blog": BG("the corpus door itself"),
    "x.ai/blog/grok-1.5": BG("model announcement - informational"),
    # ---- DeepSeek / Qwen / Kimi ----
    "2401.06066": SEAT,
    "2405.04434": SEAT,
    "2412.19437": SEAT,
    "2501.12948": ("reasoning-seat lineage for the judge pool",
                   "FreeSwarm", "quorum-n30"),
    "2309.16609": SEAT,
    "2407.10671": SEAT,
    "2412.15115": SEAT,
    "2505.09388": SEAT,
    "2308.12966": BG("vision-language - no vision organ"),
    "2501.12599": BG("RL long-context reasoning - no RL organ"),
    # ---- the rest ----
    "2310.16944": ("DPO-aligned judge seats", "QuorumSwarm", "quorum-n30"),
    "huggingface.co/blog": ("the transformers seat registry",
                            "FreeSwarm", "delivery-n50"),
    "2406.02818": ("sequential handoffs with per-step context",
                   "SWARM_PROTOCOL", "spread"),
    "2410.05229": ("brittleness-under-perturbation = THE CHAOS SWING",
                   "SwarmCert", "7-nights"),
    "2406.11794": BG("dataset-curation benchmark - informational"),
    "2402.07827": BG("multilingual coverage - informational"),
    "cohere.com/blog": BG("the corpus door itself"),
    "research.ibm.com/blog": BG("the corpus door itself"),
    "machinelearning.apple.com/research": BG("the corpus door itself"),
    "2307.01952": BG("image generation - no image organ"),
    "2403.03206": BG("image generation - no image organ"),
    "2303.17564": BG("domain-specific finance LLM - informational"),
    "2305.14314": BG("quantized tuning - no training organ"),
    "2402.13929": BG("image generation - no image organ"),
    "onnx.ai": BG("portable runtime - no onnx organ"),
}


def _key(url):
    if "/abs/" in url:
        return url.rstrip("/").split("/")[-1]
    for tail in ("building-effective-agents", "scaling-monosemanticity",
                 "developer.nvidia.com/blog", "mistral.ai/news",
                 "x.ai/blog/grok-1.5", "cohere.com/blog",
                 "huggingface.co/blog", "research.ibm.com/blog",
                 "machinelearning.apple.com/research",
                 "modelcontextprotocol.io", "onnx.ai"):
        if tail in url:
            return tail
    return url


def connect():
    rows = []
    with open(LEDGER, encoding="utf-8") as f:
        for ln in f:
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("ok"):
                if not any(r["url"] == x["url"] for x in rows):
                    rows.append(r)
    connected, background, unmapped, missing_organ = [], [], [], []
    for r in rows:
        k = _key(r["url"])
        m = DOCMAP.get(k)
        if m is None:
            unmapped.append(r["url"])
            continue
        technique, organ, gate = m
        if technique is None:
            background.append({"url": r["url"], "org": r["org"],
                               "note": gate})
            continue
        path = os.path.join(ROOT, ORGANS.get(organ, "MISSING"))
        if not os.path.exists(path):
            missing_organ.append(f"{k} -> organ {organ} MISSING")
            continue
        connected.append({"url": r["url"], "org": r["org"],
                          "technique": technique, "organ": organ,
                          "gate": gate})
    by_gate = {}
    for c in connected:
        by_gate[c["gate"]] = by_gate.get(c["gate"], 0) + 1
    state = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
             "verified": len(rows), "connected": len(connected),
             "background": len(background), "unmapped": len(unmapped),
             "organ_missing": len(missing_organ), "by_gate": by_gate,
             "law": "connected = technique + organ-on-disk + S+ gate; "
                    "everything else is named background honestly"}
    json.dump({"connected": connected, "background": background},
              open(MAP_F, "w", encoding="utf-8"), indent=1)
    json.dump(state, open(STATE_F, "w", encoding="utf-8"), indent=1)
    print(f"[connect]: verified {len(rows)} | CONNECTED to a live organ "
          f"+ gate: {len(connected)} | honest background: "
          f"{len(background)} | unmapped: {len(unmapped)} | organ-missing: "
          f"{len(missing_organ)}")
    print(f"[connect]: by S+ gate: {json.dumps(by_gate)}")
    for u in unmapped:
        print(f"  UNMAPPED-LOUD {u}")
    for m in missing_organ:
        print(f"  ORGAN-MISSING {m}")
    return state


if __name__ == "__main__":
    connect()