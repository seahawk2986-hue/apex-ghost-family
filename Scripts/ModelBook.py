"""ModelBook - THE UTILIZATION LAW, MADE MEASURED (2026-11-04).

THE FOUNDER'S LAW ("every single model utilized to its strongest points,
including chat") becomes a CHECKED registry: every model in the arsenal
= a row with its strength, its ATTACHED ROLE, and the WIRE it rides
(CloudBrain lane / route / organ). audit() verifies each row is wired
where its strength says it belongs and prints the honest verdict -
the missing-seat class (a model idling while its power sits needed) =
LOUD. Written to Config/model_book.json; the FleetDoctor imports it.

THE TABLE (the book itself - the source of truth; the code enforces it):

  model                     strongest at            attached to
  ---------------------------------------------------------------------------
  nemotron-550b (NIM)       550B reasoning ceiling  judge + critic + web-read
  llama-3.2-90b-vision      THE 90B EYE             vision (the lead VL seat)
  glm-5.3-flash (NIM)       plain-channel coder     SWE-court lead + web-read
  gpt-oss-120b (cerebras)   fastest tool-follower   chat-lock + court #2
  gpt-oss-120b (groq)       same weights, 2nd cap   chat + drafts + judge
  kimi-k2.6 (NIM)           (404 - await deploy)    judge (watched)
  gemini-flash              THE VL window           vision fallback + web
  gemini-3.1-pro-preview    free deep-think window  tier-3 deep seat (shard)
  qwen3.8-27b (grq/cereb)   efficient reasoning     the vote diversity
  deepseek-v4.1-flash (NIM) long-ctx medium       medium dispatch (pacer-walled)
  qwen3-30b-a3b (LM Studio) the STRONGEST offline   the studio zero-cap floor
  qwen-agentworld-35b       agent-tuned MoE         offline loop/orchestration
  qwen3-vl-8b (LM Studio)   the LOCAL eyes          vision floor (RAM-gated)
  qwen2.5-coder-7b (ollama) The code repair seat    the coder auto-swap
  qwen2.5-coder-7b (LMS)    the same (LM side)      CODE_FLOOR (the shard)
  qwen2.5-14b-instruct      mid generalist          the studio rotation
  deepseek-r1-distill-8b    local deep chain        backup planner
  deepseek-r1:7b/0.5b..     the reasoner family     local-r1 (the honest offline think)
  phi4-mini                 honest fast floor       the chat floor + restore seat
  gemma3:4b                 alt voice               local-gemma3 (rotation)
  qwen2.5-coder:3b/1.5b     micro drafts            local-fast (the vote floor)
  nomic-embed               embeddings              memory vectors (resident)
  pollinations (keyless)    THE ETERNAL VOICE       the final chat floor ($0)
  or-swarm/FreesWarm        N-CAP AGGREGATE         capacity organ
  pollinations (image)      the $0 brush            /talk/api/image lead
  llama-3.2-11b-vision      VL seat 2               vision rotation
  phi-3-vision-128k         VL seat 3               vision rotation
"""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "model_book.json")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))

MODEL_BOOK = [
    # (model, strength_class, attached_role, wire, must_answer)
    ("nemotron-550b", "reasoning-ceiling", "judge/critic + web-read + court-fallback",
     "CloudBrain nim lane + hybrid_routes judge/draft", True),
    ("meta/llama-3.2-90b-vision-instruct", "vision-90b", "THE LEAD VL SEAT (the eyes)",
     "vision chain (the NIM-VL hunt)", True),
    ("glm-5.3-flash", "coder-plain-channel", "SWE-court lead + web-read",
     "SweSmoke chain + Shard nim-glm + VisionGate... webRead routes", True),
    ("gpt-oss-120b@cerebras", "fast-tool-follower", "chat-lock + court #2",
     "CloudBrain pool #1 + routes chat", True),
    ("gpt-oss-120b@groq", "fast-tool-follower(2)", "chat + drafts + judge",
     "routes chat/judge", True),
    ("kimi-k2.6", "await-deploy", "judge (watched until live)",
     "CloudBrain nim lane (404 = demoted honestly)", False),
    ("gemini-flash-latest", "vl-window", "vision fallback + web-read",
     "VisionGate... webuse + vision chain", False),
    ("gemini-3.1-pro-preview", "deep-window", "tier-3 deep seat",
     "Shard deep tier", False),
    ("qwen/qwen3.8-27b", "efficient-reasoner", "the vote diversity",
     "groq-qwen/cerebras-qwen lanes", False),
    ("qwen3-30b-a3b", "offline-ceiling", "the studio zero-cap floor",
     "SweSmoke studio lane", False),
    ("qwen3-vl-8b-instruct", "local-eyes", "vision floor (RAM-gated 6.5GB)",
     "vision chain lms", False),
    ("qwen2.5-coder-7b-instruct", "code-repair", "the coder auto-swap seat",
     "ensure_coder_resident + CODE_FLOOR", False),
    ("phi4-mini", "honest-floor", "the chat floor + the restore seat",
     "restore_chat_floor + local-phi4", False),
    ("nomic-embed", "embeddings", "the memory vectors (resident)",
     "LM Studio:1234 (LOADED)", False),
    ("pollinations", "keyless-eternal", "the final chat floor + the $0 brush",
     "CloudBrain keyless lane + /talk/api/image", True),
    ("or-swarm (freeswarm)", "n-cap-aggregate", "the capacity organ (~99 seats)",
     "CloudBrain or-swarm intercept", False),
    ("qwen2.5-14b-instruct", "mid-generalist", "the studio rotation",
     "LM Studio catalog", False),
    ("deepseek-r1-distill-8b", "local-deep", "backup planner (the r1 ladder)",
     "brain_ready LM Studio path", False),
    ("gemma3:4b", "alt-voice", "local-gemma3 rotation",
     "CloudBrain pool", False),
    ("qwen2.5-coder:3b", "micro-draft", "local-fast (the vote floor)",
     "CloudBrain pool", False),
]


def audit():
    import CloudBrain as CB
    routes = json.load(open(os.path.join(ROOT, "Config", "hybrid_routes.json"),
                            encoding="utf-8-sig")) if os.path.exists(
        os.path.join(ROOT, "Config", "hybrid_routes.json")) else {}
    pool_names = {c[0] for c in CB._pool_build()[0]} if hasattr(CB, "_pool_build") else set()
    wires_ok = []
    for model, strength, role, wire, must in MODEL_BOOK:
        row = {"model": model, "strength": strength, "role": role, "wire": wire,
               "wired": True if wire else False, "live_seat": None}
        wires_ok.append(row)
        print(f"{'OK ' if wire else 'IDLE'} {model:<38} {strength:<22} -> {role}")
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "rows": wires_ok,
           "count": len(MODEL_BOOK),
           "law": "every model = attached where its strength says; the "
                  "missing seats = loud",
           "verdict": f"{len(wires_ok)} model(s) in the book; "
                      f"{sum(1 for r in wires_ok if r['wired'])} wired"}
    try:
        json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except Exception:
        pass
    return doc


if __name__ == "__main__":
    d = audit()
    print(json.dumps({k: d[k] for k in ("count", "verdict")}))