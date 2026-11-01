import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
body = {
    "title": "feat(hooks): muse provider bundle (Agent Plugins 1.0.0)",
    "head": "seahawk2986-hue:apex-fix",
    "base": "main",
    "body": ("Part 2 material for #4917 (Agent Plugins 1.0.0: "
             "plugin.json + hooks/hooks.json + the Claude-shape adapter; "
             "the parity command stays with the issue author). "
             "**Automated draft by apex-ghost-family (disclosed); "
             "founder-verified.** Coordination-first."),}
req = urllib.request.Request(
    "https://api.github.com/repos/rtk-ai/rtk/pulls",
    data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + tok,
             "Accept": "application/vnd.github+json",
             "User-Agent": "apex-one-click/1.0"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    print("PR CREATED:", d.get("html_url"))
except urllib.error.HTTPError as e:
    print("HTTPError", e.code)
    print("BODY:", e.read().decode("utf-8", "replace")[:600])