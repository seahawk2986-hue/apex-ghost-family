"""HANDOFF-STEP-4: the ACTUAL provider/model inventory (no secrets —
the shapes and the names only, to give Chad/Mica the exact routes)."""
import json
import os
import sys

import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)
sys.path.insert(0, "Scripts")
import CloudBrain as CB

# 1. the keys = the SHAPES-not-values (present/absent only)
keys = CB.env_keys()
keyflags = {k: ("PRESENT" if v else "absent") for k, v in (
    ("GROQ_API_KEY", keys.get("GROQ_API_KEY")),
    ("GEMINI_API_KEY", keys.get("GEMINI_API_KEY")),
    ("OPENROUTER_API_KEY", keys.get("OPENROUTER_API_KEY")),
    ("OLLAMA_API_KEY", keys.get("OLLAMA_API_KEY")),
    ("CLOUD_ALLOWED", keys.get("CLOUD_ALLOWED")),
    ("CREDITS_ALLOWED", keys.get("CREDITS_ALLOWED")))}
print("[key-shapes]:", json.dumps(keyflags, indent=0))

# 2. the ollama = the LOCAL stack (the actual models on disk)
try:
    tags = rq.get("http://localhost:11434/api/tags", timeout=6).json()
    print("[ollama models on disk]:",
          [m["name"] for m in tags.get("models", [])])
    ps = rq.get("http://localhost:11434/api/ps", timeout=6).json()
    print("[in-slot now]:", [m.get("name") for m in ps.get("models", [])])
except Exception as e:
    print("[ollama]", str(e)[:70])

# 3. the LM Studio (the planner/coder serve at 1234)
try:
    lms = rq.get("http://127.0.0.1:1234/v1/models", timeout=6).json()
    print("[lmstudio models]:", [m.get("id") for m in lms.get("data", [])])
except Exception as e:
    print("[lmstudio]", str(e)[:70])

# 4. the groq = the live-model check (the = the = = = = = = = = = = = = =)
try:
    g = rq.get("https://api.groq.com/openai/v1/models",
               headers={"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")},
               timeout=15)
    ids = [m.get("id") for m in g.json().get("data", [])][:40]
    print("[groq reachable, models-list]:", len(ids), "models (the 120b present:",
          "openai/gpt-oss-120b" in ids, ")")
except Exception as e:
    print("[groq]", str(e)[:70])

# 5. the routes-file (the learned chat/voice = the actual routing)
try:
    routes = json.load(open("Config/hybrid_routes.json", encoding="utf-8-sig"))
    print("[routes]:", json.dumps(routes, indent=0)[:500])
except Exception as e:
    print("[routes]", str(e)[:60])

# 6. THE INVENTORY-RECEIPT (the = the = the = = = = = = = = = = = = = = =)
inv = {"ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
       "key_shapes": keyflags,
       "providers": {
           "groq": {"url": "api.groq.com/openai/v1", "billing": "no-card-free-tier",
                    "$0": True, "primary_chat": "openai/gpt-oss-120b"},
           "gemini": {"url": "generativelanguage.googleapis.com/v1beta/openai",
                      "billing": "no-card-free-tier", "$0": True,
                      "state": "429-cooldown-observed"},
           "openrouter": {"url": "openrouter.ai/api/v1", "billing": "no-card-free",
                          "$0": True, "state": "day-quota-shaped"},
           "ollama_local": {"url": "localhost:11434", "$0": True,
                            "models_disk": "deepseek-r1:7b, gemma3:4b, "
                            "phi4-mini:latest, qwen2.5-coder:7b(:3b :1.5b), "
                            "glm-5.3-flash:cloud, deepseek-coder:6.7b",
                            "single_slot": True, "keep_alive": "1m|24h(pinned)"},
           "lmstudio_local": {"url": "127.0.0.1:1234", "$0": True,
                              "role": "planner/coder windows"},
       }}
with open(os.path.join(ROOT, "Config", "provider_inventory.json"), "w",
          encoding="utf-8") as f:
    json.dump(inv, f, indent=1)
print("[receipt] Config/provider_inventory.json = written")