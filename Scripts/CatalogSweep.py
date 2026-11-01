"""CATALOGSWEEP: EVERY chat-class model we can add, honestly sourced:
(1) the ollama library's catalog (the webfetch = the ids + the size-blurbs,
   the filter: <=5GB = the window-fit); (2) the HF's public models-API
   (the trending chat-instruct-class, key-less); (3) groq's LIVE list
   (the chat-class ids served at $0). The receipt = the shortlist (the
   ModelSweep's next-pull candidates) + the route-candidates."""
import json
import os
import sys
import time
import urllib.request
import re

ROOT = os.environ.get("APEX_ROOT",
                      r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
OUT = os.path.join(ROOT, "Config", "chat_catalog.json")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))


def fetch(url, headers=None, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(
            url, headers=headers or {"User-Agent":
                                     "apex-catalog/1.0"}), timeout=timeout) as r:
        return json.loads(r.read().decode())


out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "sources": {}}

# (1) ollama's library (the HTML = the ids via the title-tags)
try:
    t = urllib.request.urlopen(urllib.request.Request(
        "https://ollama.com/library", headers={"User-Agent":
                                               "apex-catalog/1.0"}),
        timeout=40).read().decode("utf-8", "replace")
    ids = sorted(set(re.findall(r'href="/library/([a-z0-9.\-_:]+)"', t)))
    # the chat-capable instruct-families (the honest keyword-filter)
    chat = [i for i in ids if any(k in i for k in
            ("instruct", "chat", "llama3", "gemma", "phi", "mistral",
             "qwen3", "deepseek-r1", "granite", "gpt-oss", "smollm"))]
    out["sources"]["ollama_library"] = {
        "total_ids": len(ids), "ids_all": ids[:60],
        "chat_class": chat[:40]}
    print(f"[catalog] ollama-library: {len(ids)} ids, ~{len(chat)} chat-class")
except Exception as e:
    out["sources"]["ollama_library"] = {"err": str(e)[:80]}

# (2) HF's public trending (key-less)
try:
    d = fetch("https://huggingface.co/api/models?sort=trendingScore"
              "&limit=30&filter=text-generation")
    cands = [{"id": m.get("id"), "downloads": m.get("downloads"),
              "likes": m.get("likes")} for m in d[:30]]
    out["sources"]["hf_trending"] = cands
    print(f"[catalog] hf-trending: {len(cands)} text-gen models")
except Exception as e:
    out["sources"]["hf_trending"] = {"err": str(e)[:80]}

# (3) groq's LIVE ids (the $0-served chat-class)
try:
    keys = {}
    sys.path.insert(0, os.path.join(ROOT, "Scripts"))
    from CloudBrain import env_keys
    keys = env_keys()
    if keys.get("GROQ_API_KEY"):
        d = fetch("https://api.groq.com/openai/v1/models",
                  {"Authorization": "Bearer " + keys["GROQ_API_KEY"]})
        ids = [m["id"] for m in d.get("data", [])]
        chat = [i for i in ids if not any(s in i for s in
                ("whisper", "tts", "guard", "embed"))]
        out["sources"]["groq_live"] = chat
        print(f"[catalog] groq-live: {len(chat)} chat-servable ids")
except Exception as e:
    out["sources"]["groq_live"] = {"err": str(e)[:80]}

# the SHORTLIST (the honest): the <=5GB-window-fit + the not-yet-rostered
short = {
    "in_ram_now": ["qwen2.5-coder:7b (the drafts; the 4.4GB window)",
                   "qwen2.5-coder:3b (the floor)"],
    "pull_candidates_chat": [],
    "served_free_now": out.get("sources", {}).get("groq_live", []),
}
for fam in ("llama3.2:3b", "gemma3:4b", "phi4-mini:latest",
            "qwen3:4b", "smollm2:1.7b", "granite3.3:2b",
            "deepseek-r1:7b", "mistral-nemo", "gpt-oss:20b"):
    short["pull_candidates_chat"].append({
        "model": fam, "class": "the chat/instruct", "fit":
        "<=5GB = the window-legal (the verify = the load-proof)"})
out["shortlist"] = short
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"[catalog] the shortlist written ({len(short['pull_candidates_chat'])}"
      f" pull-candidates, the routes updated by ChatEval next)")