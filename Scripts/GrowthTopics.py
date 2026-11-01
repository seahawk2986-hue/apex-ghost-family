import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

TOPICS = {
    "seahawk2986-hue/apex-ghost-family": [
        "ai-agents", "automation", "agent-framework", "mcp", "mcp-server",
        "ai-agents-earn", "honest-agents", "autonomous-agents",
        "quality-gates", "swe-agent", "bug-triage", "open-source"],
    "seahawk2986-hue/seahawk2986-hue": [
        "apex-ghost-family", "ai-agents", "automated-contributors",
        "agent-shop", "honest-automation"],
}
for repo, names in TOPICS.items():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/topics",
        data=json.dumps({"names": names}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-growth/1.0"}, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[growth] {repo}: topics set -> {names}")
    except Exception as e:
        print(f"[growth] {repo}: {str(e)[:50]}")
# the receipt
with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": "upward", "what": "the growth-topics set "
                        "(the SEO/discovery class's first applied move)"})
            + "\n")
print("the marketing-canon's #1 lesson applied live")