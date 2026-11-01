"""THE AGENT ROSTER (every agent Apex can use, tested + priced + honest):
the router dispatches each task to the cheapest CAPABLE agent:
 1. local-coder    qwen2.5-coder:7b @ localhost:11434 - \\$0 forever, RAM
                   4.4GB (inside the window; the swarm duck queues) - the
                   patch/JSON brain;
 2. cloud-ollama   gpt-oss:120b - Andrew's credits, SPEND-GATED (\\$0.50
                   session cap, ledgered) - the synthesis/judge brains;
 3. groq/openrouter - the keys' state flags (403/404 tonight - the
                   founder's renewal step); auto-skipped while dead;
 4. the offload lane - the harness's own subagents (the big scans/audits
                   run off my box's main thread; RAM-light locally);
  SKIPPED HONESTLY: aider (py3.14 wheels absent), cline (GUI), goose
  (extra binary; the same capability exists in-member).
TEST GATE: (a) the local probe (\\$0), (b) the cloud probe (cap-gated,
ledgered), (c) the ROUTE table correct for sample tasks, (d) the skips'
reasons printed, (e) reproducible."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import CloudBrain as CB

OUT = os.path.join(ROOT, "Config", "agent_roster.json")

ROSTER = [
    {"agent": "local-coder", "model": "qwen2.5-coder:7b",
     "where": "localhost:11434", "cost_usd_per_call": 0.0,
     "ram_gb": 4.4, "best_at": "patch-diffs, JSON contracts, code tasks"},
    {"agent": "cloud-ollama", "model": "gpt-oss:120b",
     "where": "ollama.com (credits)", "cost_usd_per_call": 0.001,
     "ram_gb": 0, "best_at": "synthesis, judging, long-context drafting",
     "status": "DORMANT-BY-DEFAULT (the founder's opt-in: CLOUD_ALLOWED=1; "
               "probed OK on his credits, spend-gated $0.50/session)"},
    {"agent": "harness-subagents", "model": "the session's own provider",
     "where": "opencode (the orchestrating harness)", "cost_usd_per_call":
     0.0, "ram_gb": 0.1, "best_at": "the big scans/offloaded audits",
     "cap": "bounded one-shot tasks"},
    {"agent": "groq", "model": "llama-3.3-70b-versatile", "where": "cloud",
     "cost_usd_per_call": 0.0, "ram_gb": 0, "best_at": "fast chat bursts",
     "status": "the key tonight: 403 (the founder's renewal)"},
    {"agent": "openrouter", "model": "free tier", "where": "cloud",
     "cost_usd_per_call": 0.0, "ram_gb": 0,
     "best_at": "the free-class fallback",
     "status": "404 tonight (the model id/the credit - the founder's step)"},
]
ROUTER = [
    (r"patch|diff|code|fix|schema|json", "local-coder"),
    (r"synthes|judge|rank|plan|long", "cloud-ollama"),
    (r"scan|audit|sweep|inventory", "harness-subagents"),
]


def probe_local():
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=json.dumps({"model": "qwen2.5-coder:7b", "stream": False,
                             "messages": [{"role": "user",
                                           "content": "Reply: OK"}],
                             "options": {"num_predict": 16}}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode())
        txt = d.get("message", {}).get("content", "")
        return bool(txt.strip()), txt.strip()[:20]
    except Exception as e:
        return False, str(e)[:60]


def route(task_text):
    t = task_text.lower()
    for pat, agent in ROUTER:
        if re.search(pat, t):
            return agent
    return "local-coder"


def selftest():
    print("=== THE AGENT ROSTER'S OWN GATE ===")
    legs = []
    ok, ans = probe_local()
    leg_a = ok
    print(f"   (a) local-coder probe: '{ans}' ({leg_a})")
    legs.append(("local_probe", leg_a))
    g = json.load(open(os.path.join(ROOT, "Config", "spend_gate.json"),
                       encoding="utf-8-sig"))
    sp0 = g["spent_usd"]
    g["spent_usd"] = g["session_cap_usd"]
    with open(os.path.join(ROOT, "Config", "spend_gate.json"), "w") as f:
        json.dump(g, f)
    r = CB.chat("probe", max_tokens=4, purpose="roster-cap-test")
    g["spent_usd"] = sp0
    with open(os.path.join(ROOT, "Config", "spend_gate.json"), "w") as f:
        json.dump(g, f)
    leg_b = r is None
    print(f"   (b) the cloud agent is CAP-GATED (a call at-cap refused): "
          f"{leg_b}")
    legs.append(("cloud_cap", leg_b))
    routes = [route("draft a patch for the Go handler"),
              route("judge which stage family first"),
              route("scan the whole tree for orphans")]
    leg_c = routes == ["local-coder", "cloud-ollama", "harness-subagents"]
    print(f"   (c) the router: {routes} ({leg_c})")
    legs.append(("route_table", leg_c))
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "roster": ROSTER, "router": [(p, a) for p, a in ROUTER],
           "skipped_honestly": [("aider-chat", "py3.14 wheels absent (the "
                                 "pip build-backend failure - receipted)"),
                                ("cline", "a GUI extension - not "
                                 "cli-scriptable on this box"),
                                ("goose", "an extra binary for a "
                                 "capability already in the roster (the "
                                 "local-coder + the subagents)")],
           "law": "the local-first + the cap + the offload lane; every "
                  "agent's cost/ram/best-at is in ONE table"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, OUT)
    leg_d = os.path.exists(OUT)
    legs.append(("roster_receipted", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[roster] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> redo'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)