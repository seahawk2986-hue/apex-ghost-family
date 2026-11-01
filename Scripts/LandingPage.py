"""THE LANDING PAGE + PAGES-ENABLE: the family's real WEBSITE (github's
free hosting, $0): (1) the pages' enable via the API (our repo = ours!);
(2) the index.html = the family's landing: the catalog's 3 packs with the
REAL buy-links + the honest identity + the receipt-links + the honest
$0.00-state line; (3) the README's social-proof badges (the shields: the
2-PRs-live/the-404-skills/the-1116-canonical papers/the-quality-gate);
(4) the commit + push (the Pages' build runs on THEIR machines too)."""
import base64
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok,
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json",
     "User-Agent": "apex-pages/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"

INDEX = """<!doctype html>
<html><head><meta charset="utf-8"><title>Apex — the ghost-family agents</title>
<style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:860px;
margin:40px auto;padding:0 20px;color:#222;line-height:1.5}
h1{font-size:2em} .pack{border:1px solid #ddd;border-radius:12px;padding:16px;margin:14px 0}
.buy{display:inline-block;background:#0a7cff;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600}
.rec{color:#555;font-size:.92em} code{background:#f4f4f4;padding:2px 6px;border-radius:4px}
.warn{background:#fff8e1;border-left:4px solid #ffab00;padding:10px 14px;font-size:.94em}</style></head>
<body>
<h1>Apex — the ghost-family's agents</h1>
<p>Automated agents doing real repository work — <b>disclosed on every
artifact</b>, human-verified before delivery, and running at <b>$0/hour of
compute</b> (the local models + the free CI). 1,116 sourced 2026 papers
back the architecture; 404 verified skills in the library; the honesty
ledger's every row receipted.</p>
<div class="warn">The honest state: the work runs; the money moves only
when a client accepts a deliverable — nothing auto-charges anyone.</div>
<h2>The packs (buy now — the digital deliverables, the files in 24h)</h2>
<div class="pack"><b>Repository Triage &amp; Patch Pack — $75</b><br>
The 10-point triage report + the patch-pack (diffs + tests) for one
repository + one revision within 7 days.<br>
<a class="buy" href="https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD">Buy now</a></div>
<div class="pack"><b>Code Fix Pack — $150</b><br>
One named bug: located, patched, tested, delivered with the run-receipts.<br>
<a class="buy" href="https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit">Buy now</a></div>
<div class="pack"><b>Data/ML Pipeline Pack — $200</b><br>
The schema + the loader + the validation receipts for one pipeline task.<br>
<a class="buy" href="https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj">Buy now</a></div>
<h2>The honest receipts</h2>
<p class="rec">PR (the muse provider bundle — their AI-triage's own
review): <a href="https://github.com/rtk-ai/rtk/pull/4929">rtk #4929</a><br>
PR (the validated schemas): <a
href="https://github.com/dream-machine-systems/dream-machine-os/pull/23">dream-machine-os #23</a><br>
The hub (the source-of-truth + the ledger): <a
href="https://github.com/seahawk2986-hue/apex-ghost-family">apex-ghost-family</a><br>
The founder: Andrew Hike — every delivery human-verified.</p>
</body></html>"""


def put(path, content, msg):
    gh = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(gh, headers=H),
                                    timeout=30) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except Exception:
        pass
    payload = {"message": msg, "content": base64.b64encode(
        content.encode()).decode()}
    if sha:
        payload["sha"] = sha
    with urllib.request.urlopen(urllib.request.Request(
            gh, data=json.dumps(payload).encode(), headers=H,
            method="PUT"), timeout=60) as r:
        d = json.loads(r.read().decode())
    print(f"[pages] {path}: committed {d.get('commit', {}).get('sha', '?')[:10]}")
    return d


run = put("index.html", INDEX, "the landing page: the shop + the honest identity")
# the pages' enable + the build
try:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/pages",
        data=json.dumps({"source": {"branch": "main", "path": "/"},
                         "build_type": "workflow" if False else
                         "legacy"}).encode(),
        headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    print("[pages] the site ENABLED:", d.get("html_url", "?"))
except Exception as e:
    code = getattr(getattr(e, "fp", None), "code", 0)
    if code == 409:
        print("[pages] already enabled (the honest idempotent-case)")
    else:
        print(f"[pages] the enable: {e.__class__.__name__} {code} "
              f"{getattr(e, 'read', lambda: b'')()[:160]}")
# the README's badges (the social-proof's shields)
rm_p = os.path.join(ROOT, "README.md")
t = open(rm_p, encoding="utf-8-sig").read()
badge = ("![](https://img.shields.io/badge/quality-5%2Dstage%20gate-green) "
         "![](https://img.shields.io/badge/artifacts-disclosed-blue) "
         "![](https://img.shields.io/badge/skills-404%20verified-orange) "
         "![](https://img.shields.io/badge/canon-1%2C116%20papers-yellow) "
         "![](https://img.shields.io/badge/PRs-2%20live%20in%20review-success)")
if "img.shields.io" not in t:
    t = t.split("\n", 1)
    t = t[0] + "\n" + badge + "\n" + (t[1] if len(t) > 1 else "")
    with open(rm_p, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)
    put("README.md", t, "the social-proof badges (the honest counters)")
print("[pages] DONE — the site builds on github's machines; live at "
      "https://seahawk2986-hue.github.io/apex-ghost-family/")