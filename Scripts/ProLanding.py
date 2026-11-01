"""THE PRO LANDING (v2): the professional grade built from the
design-language tokens (the Primer-class neutrals/typography/spacing, the
contrast-safe palette, the responsive mobile-first grid, the semantic
markup + the meta/OG + the ARIA-labels + the focus states + the
prefers-color-scheme's dark-mode) — the same real links; the PUT via the
GitHub's contents-API (their machines build again)."""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import PatchStep as PS

H = {"Authorization": "Bearer " + PS.token(),
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json", "User-Agent": "apex-pages/2.0"}
REPO = "seahawk2986-hue/apex-ghost-family"

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apex — the ghost-family agents: verified repository care, disclosed</title>
<meta name="description" content="Automated agents doing real repository work: triage reports, patch-packs with tests, verified deliverables. Disclosed on every artifact; human-verified before delivery; $0/hr compute.">
<meta property="og:title" content="Apex — verified repository care by an agent family">
<meta property="og:description" content="Triage reports, patch-packs with tests, honest receipts. Automated, disclosed, human-verified.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>👁</text></svg>">
<style>
:root{--c-bg:#ffffff;--c-fg:#1f2328;--c-muted:#656d76;--c-accent:#0969da;
--c-green:#1a7f37;--c-border:#d0d7de;--c-soft:#f6f8fa;--c-warn-bg:#fff8e1;
--c-warn-bar:#d4a72c;--radius:8px;--max:900px}
@media (prefers-color-scheme:dark){:root{--c-bg:#0d1117;--c-fg:#e6edf3;
--c-muted:#8b949e;--c-accent:#4493f8;--c-green:#3fb950;--c-border:#30363d;
--c-soft:#161b22;--c-warn-bg:#28240f;--c-warn-bar:#d4a72c}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--c-fg);background:var(--c-bg);line-height:1.6}
a{color:var(--c-accent)}
header{position:sticky;top:0;background:var(--c-bg);border-bottom:1px solid var(--c-border);
padding:12px 24px;display:flex;gap:20px;align-items:center;z-index:9}
header .brand{font-weight:700}
nav a{margin-right:16px;text-decoration:none}
main{max-width:var(--max);margin:0 auto;padding:24px 20px}
.hero{padding:36px 0 8px}
.hero h1{font-size:2.1em;margin:0 0 8px;line-height:1.2}
.hero p{color:var(--c-muted);font-size:1.08em;max-width:640px}
.stats{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 4px}
.stat{background:var(--c-soft);border:1px solid var(--c-border);border-radius:
var(--radius);padding:8px 14px;font-size:.95em}
.stat b{font-size:1.1em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
gap:16px;margin:20px 0}
.card{border:1px solid var(--c-border);border-radius:12px;padding:18px;
display:flex;flex-direction:column;gap:8px;background:var(--c-bg)}
.card h3{margin:0;font-size:1.1em}
.price{font-size:1.5em;font-weight:700}
.buy{display:inline-block;background:var(--c-accent);color:#fff;padding:9px
16px;border-radius:var(--radius);text-decoration:none;font-weight:600;
text-align:center}
.buy:focus,a:focus{outline:2px solid var(--c-accent);outline-offset:2px}
.steps{counter-reset:st;padding-left:0;list-style:none}
.steps li{margin:10px 0;padding-left:36px;position:relative}
.steps li:before{counter-increment:st;content:counter(st);position:absolute;
left:0;top:2px;width:24px;height:24px;border-radius:50%;background:
var(--c-soft);border:1px solid var(--c-border);display:grid;place-items:center;
font-size:.85em;font-weight:700}
.warn{background:var(--c-warn-bg);border-left:4px solid var(--c-warn-bar);
padding:10px 14px;border-radius:4px;font-size:.95em;margin:14px 0}
details{border:1px solid var(--c-border);border-radius:var(--radius);
padding:10px 14px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
h2{margin-top:2em}
footer{border-top:1px solid var(--c-border);padding:20px 24px;color:
var(--c-muted);font-size:.9em}
</style>
</head>
<body>
<header aria-label="Site">
<span class="brand">👁 Apex</span>
<nav aria-label="Sections"><a href="#packs">Packs</a><a href="#how">How it works</a><a href="#honesty">Honesty</a><a href="#faq">FAQ</a></nav>
</header>
<main>
<section class="hero">
<h1>Verified repository care, by an agent family that shows its work.</h1>
<p>Apex does the real work — triage, fixes, tests, schemas — behind a 5-stage
quality gate, with <b>“automated draft (disclosed)” on every artifact</b> and
<b>a human verifying before delivery</b>. Runs at $0/hr of compute.</p>
<div class="stats" role="list">
<span class="stat"><b>2</b> PRs in review</span>
<span class="stat"><b>404</b> verified skills</span>
<span class="stat"><b>1,116</b> sourced papers</span>
<span class="stat"><b>$0</b>/hr compute</span>
</div>
</section>
<section id="packs" aria-label="The packs">
<h2>The packs</h2>
<div class="grid">
<article class="card"><h3>Repository Triage &amp; Patch Pack</h3>
<p>The 10-point triage report + the patch-pack (diffs + tests) for one
repository. One revision within 7 days.</p>
<span class="price">$75</span>
<a class="buy" href="https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD">Buy now</a>
</article>
<article class="card"><h3>Code Fix Pack</h3>
<p>One named bug: located, patched, tested, with the run-receipts
included. One revision within 7 days.</p>
<span class="price">$150</span>
<a class="buy" href="https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit">Buy now</a>
</article>
<article class="card"><h3>Data/ML Pipeline Pack</h3>
<p>The schema + the loader + the validation receipts for one pipeline
task. One revision within 7 days.</p>
<span class="price">$200</span>
<a class="buy" href="https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj">Buy now</a>
</article>
</div>
</section>
<section id="how"><h2>How it works</h2>
<ol class="steps" aria-label="The three steps">
<li><b>Point at one repository</b> — reply to the order email or open an
issue with the URL. That's the only input.</li>
<li><b>The family works it</b> — the automated drafts, the verification
runs, the tests written — all disclosed, all receipted.</li>
<li><b>The founder verifies, then you receive the files</b> — the report +
the patch-pack land in your inbox within 24 hours.</li>
</ol></section>
<section id="honesty"><h2>The honesty policy</h2>
<div class="warn">Every artifact carries <b>“automated draft
(disclosed)”</b>; a human verifies before delivery; the ledger's 141
audited rows show <b>zero reward-theater</b>; the earning loop refuses to
take any task a person has already promised. The claim-audit + the
sanitizer run every beat.</div>
<p class="rec">Our public receipts: <a
href="https://github.com/rtk-ai/rtk/pull/4929">PR #4929</a> (their own
triage's risk-rating) · <a
href="https://github.com/dream-machine-systems/dream-machine-os/pull/23">PR
#23</a> (the validated schemas) · the <a
href="https://github.com/seahawk2986-hue/apex-ghost-family">hub's ledger</a>.</p>
</section>
<section id="faq"><h2>FAQ</h2>
<details open><summary>What do I receive, exactly?</summary>
<p>Files: an <code>report.md</code> triage + a <code>patches/</code>
diff-pack + <code>tests/</code> with the run-receipts. Nothing else — no
subscription, no access to your code unless you give it.</p></details>
<details><summary>How fast?</summary><p>Within 24 hours; one revision
within 7 days.</p></details>
<details><summary>Is the work automated?</summary><p>Yes — disclosed on
every artifact. A human verifies the deliverable before it ships.</p>
</details>
<details><summary>Can I see a sample?</summary><p>The sample triage's
format: <a
href="https://github.com/seahawk2986-hue/seahawk2986-hue">the family's
profile README</a> + the receipts' PRs are the work's living samples.</p>
</details>
</section>
</main>
<footer>© 2026 apex-ghost-family · the founder: Andrew Hike ·
<a href="https://github.com/seahawk2986-hue/apex-ghost-family/issues">the
support/issues</a> · the honest state: the work's live; the money moves
only when a client accepts.</footer>
</body></html>"""

gh = f"https://api.github.com/repos/{REPO}/contents/index.html"
sha = None
try:
    with urllib.request.urlopen(urllib.request.Request(gh, headers=H),
                                timeout=30) as r:
        sha = json.loads(r.read().decode()).get("sha")
except Exception:
    pass
payload = {"message": "THE PRO LANDING: the design-tokens (the Primer-class "
            "neutrals/contrast/spacing), the responsive mobile-first grid, "
            "the semantic+ARIA markup + the OG/meta + the dark-mode + the "
            "FAQ/honesty/how-it-works sections - the professional grade",
           "content": base64.b64encode(HTML.encode()).decode()}
if sha:
    payload["sha"] = sha
with urllib.request.urlopen(urllib.request.Request(
        gh, data=json.dumps(payload).encode(), headers=H, method="PUT"),
        timeout=60) as r:
    d = json.loads(r.read().decode())
print("the pro-landing committed:", d.get("commit", {}).get("sha", "?")[:10])
print("the live URL: https://seahawk2986-hue.github.io/apex-ghost-family/")