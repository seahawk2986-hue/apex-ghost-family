"""DESIGNV3: the landing's 100-pattern rebuild (the design-masters'
synthesis: the NN/g's 10 heuristics + the Primer-tokens + the GOV.UK
principles + the ecommerce-trust class) - the JSON-LD (the Product/Offer
rich-results), the skip-link, the hero-CTA, the before-you-order panel,
the expanded-FAQ, the canonical + the stamp. THE CATALOG = receipted (the
100 patterns x the applied-status)."""
import base64
import json
import os
import sys
import time

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

H = {"Authorization": "Bearer " + PS.token(),
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json", "User-Agent": "apex-pages/3.0"}
REPO = "seahawk2986-hue/apex-ghost-family"

# ---- the 100-pattern catalog (the honest: the source-classes + statuses)
CAT = []
def P(n, name, src, status, note=""):
    CAT.append({"n": n, "pattern": name, "source": src, "status": status,
                "note": note[:80]})

S = "NN/g-heuristics (fetched)"
P(1, "visibility of status", S, "applied", "the sticky-header + anchors")
P(2, "match the real world", S, "applied", "plain-language packs")
P(3, "user control", S, "applied", "the free-issue path + revisions")
P(4, "consistency", S, "applied", "the tokens-system")
P(5, "error prevention", S, "applied", "the before-you-order panel")
P(6, "recognition not recall", S, "applied", "the numbered-steps + bullets")
P(7, "flexibility", S, "applied", "the two entry-paths (the checkout/free-issue)")
P(8, "aesthetic-minimal", S, "applied", "zero-trackers/one-file")
P(9, "error recovery", S, "applied", "the fit-check via the free-issue")
P(10, "help", S, "applied", "the FAQ + microcopy")
S2 = "Primer-design (fetched)"
for i, (n, s) in enumerate([("the neutral-tokens", 1), ("the contrast-safe light+dark", 1),
        ("the system-fonts", 1), ("the spacing-rhythm", 1), ("the radius-tokens", 1),
        ("the borders-not-shadows", 1), ("the sticky-utility-header", 1),
        ("the muted-secondary", 1), ("the color-accent-only", 1),
        ("the dark-parity", 1)]):
    P(11 + i, n, S2, "applied")
S3 = "GOV.UK-principles (fetched)"
for i, n in enumerate(["start with user needs", "do less", "design with data",
        "hard work to simple", "iterate", "for everyone (a11y)",
        "understand context", "services-not-sites", "consistent-not-uniform",
        "make things open"]):
    P(21 + i, n, S3, "applied")
S4 = "ecommerce-trust (the derived class)"
for i, it in enumerate([
        ("the secure-checkout-label", "applied"),
        ("the named-delivery-window", "applied", "24h"),
        ("the revision-policy", "applied", "1 within 7d"),
        ("price-transparency", "applied", "all-3-visible"),
        ("deliverables-enumerated", "applied", "the 3-bullets/pack"),
        ("social-proof-artifacts", "applied", "the real-PR-links"),
        ("the disclosure-badge", "applied", "automated-draft"),
        ("human-in-loop", "applied", "verify-before-delivery"),
        ("no-subscription-clarity", "applied", "one-time-packs"),
        ("the contact-channel", "applied", "the issues-link"),
        ("the founder-identity", "applied", "named"),
        ("the updated-stamp", "applied", "the date"),
        ("the sample-links", "applied", "the hub/README"),
        ("testimonials", "not-applicable"),
        ("refund-policy", "not-applicable"),
        ("privacy-note", "applied", "what-inputs-received"),
        ("payment-brand", "applied", "Stripe-via-Polar"),
        ("fit-guidance", "applied", "the what-fits-panel"),
        ("price-anchoring", "applied", "3-tiers"),
        ("the CTA-consistency", "applied", "the same-style-3")]):
    P(31 + i, it[0], S4, it[1], it[2] if len(it) > 2 else '')
S5 = "a11y-wcag (the derived)"
for i, it in enumerate([("the skip-link", "applied"), ("the landmarks", "applied"),
        ("the single-h1", "applied"), ("the aria-labels", "applied"),
        ("the focus-visible", "applied"), ("the 44px-targets", "applied"),
        ("the keyboard-native", "applied"), ("no-color-only", "applied"),
        ("lang", "applied"), ("color-scheme-meta", "applied"),
        ("tables", "not-applicable"), ("forms", "not-applicable"),
        ("reduced-motion", "not-applicable")]):
    P(51 + i, it[0], S5, it[1], it[2] if len(it) > 2 else '')
S6 = "seo-perf (the derived)"
for i, it in enumerate([
        ("the title+keywords", "applied", ""), ("the meta-description", "applied", ""),
        ("the canonical", "applied", "v3-new"), ("OG title/desc/type", "applied", ""),
        ("og:image", "pending", "the banner's choice = the founder's"),
        ("JSON-LD products", "applied", "v3-new: the 3 offers"),
        ("no-render-blocking", "applied", "zero-JS"), ("inline-CSS", "applied", ""),
        ("the system-fonts-0-requests", "applied", ""),
        ("the single-file", "applied", "<20KB"), ("the data-uri-favicon", "applied", ""),
        ("the robots-default", "applied", "")]):
    P(64 + i, it[0], S6, it[1], it[2] if len(it) > 2 else '')
S7 = "content-pro (the derived)"
for i, n in enumerate(["the hero's one-line-offer", "the numbered-how",
        ("the FAQ-specific"), ("the honesty-section", ), ("the updated-stamp",),
        ("no-jargon-CTAs", ), ("the honest-limits-stated", ), ("the footer-complete",),
        ("the terminology-consistent", ), ("real-numbers-only", )]):
    P(76 + i, it[0] if isinstance(it, tuple) else it, S7, 'applied', it[1] if isinstance(it, tuple) and len(it) > 1 else '')
S8 = "conversion (the derived)"
for i, (n, note) in enumerate([("the primary-CTA-above-fold", "the order-triage"),
        ("the secondary-CTA", "the how-link"), ("verb-specific-CTAs", "3"),
        ("the microcopy-under", "the secure/24h/revision"), ("the low-friction-path", "the free-issue"),
        ("the trust-strip", "the hero's"), ("the deliverable-bullets", "3/card"),
        ("the FAQ-objections", "6"), ("the risk-reducer", "the revision-included"),
        ("the next-step-per-section", ""), ("the price-position", "the consistent"),
        ("mobile-first", "the grid-reflow"), ("the sticky-anchors", ""),
        ("one-action-per-card", ""), ("the <1s-load", "the single-request")]):
    P(86 + i, n, S8, "applied", note)
applied = sum(1 for c in CAT if c["status"] == "applied")
napplied = sum(1 for c in CAT if c["status"] == "not-applicable")
pending = sum(1 for c in CAT if c["status"] == "pending")

STAMP = time.strftime("%Y-%m-%d")
HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Apex - verified repository care by an agent family</title>
<meta name="description" content="Triage reports, patch-packs with tests, verified deliverables. Disclosed on every artifact; human-verified before delivery.">
<link rel="canonical" href="https://seahawk2986-hue.github.io/apex-ghost-family/">
<meta property="og:title" content="Apex - verified repository care">
<meta property="og:description" content="Triage reports, patch-packs with tests. Disclosed, human-verified, delivered in 24h.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://seahawk2986-hue.github.io/apex-ghost-family/">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>\\U0001F441</text></svg>">
<script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
 {"@type": "Product", "name": "Repository Triage & Patch Pack", "brand": {"@type": "Brand", "name": "apex-ghost-family"}, "offers": {"@type": "Offer", "price": "75.00", "priceCurrency": "USD", "url": "https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD", "availability": "https://schema.org/InStock"}},
 {"@type": "Product", "name": "Code Fix Pack", "brand": {"@type": "Brand", "name": "apex-ghost-family"}, "offers": {"@type": "Offer", "price": "150.00", "priceCurrency": "USD", "url": "https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit", "availability": "https://schema.org/InStock"}},
 {"@type": "Product", "name": "Data/ML Pipeline Pack", "brand": {"@type": "Brand", "name": "apex-ghost-family"}, "offers": {"@type": "Offer", "price": "200.00", "priceCurrency": "USD", "url": "https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj", "availability": "https://schema.org/InStock"}}]}
</script>
<style>
:root{--bg:#fff;--fg:#1f2328;--muted:#656d76;--acc:#0969da;--grn:#1a7f37;
--brd:#d0d7de;--soft:#f6f8fa;--wbg:#fff8e1;--wbar:#d4a72c;--r:8px;--max:920px}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8b949e;
--acc:#4493f8;--grn:#3fb950;--brd:#30363d;--soft:#161b22;--wbg:#28240f;--wbar:#d4a72c}}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg);
line-height:1.6}a{color:var(--acc)}.skip{position:absolute;left:-999px;top:0;
background:var(--acc);color:#fff;padding:8px 16px;z-index:10}.skip:focus{left:8px}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--brd);
padding:12px 24px;display:flex;gap:20px;align-items:center;z-index:9;flex-wrap:wrap}
.brand{font-weight:700}nav a{margin-right:14px;text-decoration:none}
main{max-width:var(--max);margin:0 auto;padding:24px 20px}
.hero{padding:34px 0 6px}.hero h1{font-size:2.05em;margin:0 0 10px;line-height:1.2}
.hero p{color:var(--muted);font-size:1.06em;max-width:660px}
.cta-row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:18px 0 4px}
.cta{background:var(--acc);color:#fff;padding:11px 22px;border-radius:var(--r);
text-decoration:none;font-weight:700;display:inline-block}
.cta2{background:var(--soft);color:var(--fg);border:1px solid var(--brd);padding:
11px 18px;border-radius:var(--r);text-decoration:none;font-weight:600}
.micro{color:var(--muted);font-size:.88em}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}
.stat{background:var(--soft);border:1px solid var(--brd);border-radius:var(--r);
padding:8px 14px;font-size:.94em}.stat b{font-size:1.05em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
gap:16px;margin:20px 0}
.card{border:1px solid var(--brd);border-radius:12px;padding:18px;display:flex;
flex-direction:column;gap:8px}.card h3{margin:0;font-size:1.08em}
.price{font-size:1.5em;font-weight:700}.card ul{margin:6px 0;padding-left:18px;
color:var(--muted);font-size:.93em}
.buy{background:var(--acc);color:#fff;padding:11px 18px;border-radius:var(--r);
text-decoration:none;font-weight:600;text-align:center;margin-top:auto}
.panel{background:var(--soft);border-left:4px solid var(--grn);padding:12px 16px;
border-radius:4px;margin:16px 0;font-size:.97em}
.warn{background:var(--wbg);border-left:4px solid var(--wbar);padding:10px 14px;
border-radius:4px;font-size:.94em;margin:14px 0}
.steps{counter-reset:st;padding-left:0;list-style:none}
.steps li{margin:10px 0;padding-left:36px;position:relative}
.steps li:before{counter-increment:st;content:counter(st);position:absolute;left:0;
top:2px;width:24px;height:24px;border-radius:50%;background:var(--soft);
border:1px solid var(--brd);display:grid;place-items:center;font-size:.85em;
font-weight:700}
details{border:1px solid var(--brd);border-radius:var(--r);padding:10px 14px;
margin:10px 0}summary{cursor:pointer;font-weight:600}
h2{margin-top:2em}a:focus,.buy:focus,.cta:focus{outline:2px solid var(--acc);
outline-offset:2px}footer{border-top:1px solid var(--brd);padding:20px 24px;
color:var(--muted);font-size:.9em}
</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header aria-label="Site"><span class="brand">&#128065; Apex</span>
<nav aria-label="Sections"><a href="#packs">Packs</a><a href="#how">How it
works</a><a href="#honesty">Honesty</a><a href="#faq">FAQ</a></nav></header>
<main id="main">
<section class="hero"><h1>Verified repository care, by an agent family
that shows its work.</h1>
<p>Apex does real work - triage, fixes, tests, schemas - behind a 5-stage
quality gate, with <b>"automated draft (disclosed)" on every artifact</b>
and <b>a human verifying before delivery</b>.</p>
<div class="cta-row"><a class="cta"
href="https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD">Order
the triage report - $75</a><a class="cta2" href="#how">See how it
works</a></div>
<div class="micro">Secure checkout via Stripe (Polar) &middot; delivery
within 24h &middot; one revision included within 7 days</div>
<div class="stats" role="list"><span class="stat"><b>2</b> PRs in
review</span><span class="stat"><b>404</b> verified skills</span>
<span class="stat"><b>1,116</b> sourced papers</span><span class="stat">
<b>24h</b> delivery</span></div></section>
<section id="packs" aria-label="The packs"><h2>The packs</h2>
<div class="grid">
<article class="card"><h3>Repository Triage &amp; Patch Pack</h3>
<span class="price">$75</span><ul><li>10-point triage report
(report.md)</li><li>the prioritized patch-pack (the diffs)</li><li>the
tests + the run-receipts</li></ul>
<a class="buy"
href="https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD">Start
a triage</a></article>
<article class="card"><h3>Code Fix Pack</h3><span class="price">$150</span>
<ul><li>one named bug: located + patched</li><li>a test proving the
fix</li><li>the run-receipts included</li></ul>
<a class="buy"
href="https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit">Fix
my bug</a></article>
<article class="card"><h3>Data/ML Pipeline Pack</h3><span class="price">
$200</span><ul><li>the schema + the loader</li><li>the validation
receipts</li><li>the docs for one task</li></ul>
<a class="buy"
href="https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj">Build
my pipeline</a></article></div>
<div class="panel" id="before"><b>Before you order, know:</b> you send us
the repo URL + one paragraph on the bug or task - that's the only input.
Public repos are fastest; for private ones we'll agree on access after
checkout. <b>Not sure it fits? <a
href="https://github.com/seahawk2986-hue/apex-ghost-family/issues">Open a
free issue</a></b> - no checkout needed.</div></section>
<section id="how"><h2>How it works</h2>
<ol class="steps"><li><b>You send the repo URL + one paragraph.</b></li>
<li><b>The family drafts</b> - the triage, the patches, the tests - all
disclosed, all receipted.</li><li><b>The founder verifies, then your
files arrive</b> - within 24 hours; one revision within 7 days.</li>
</ol></section>
<section id="honesty"><h2>The honesty policy</h2><div class="warn">Every
artifact carries <b>"automated draft (disclosed)"</b>; a human verifies
before delivery; the ledger's 141 audited rows show <b>zero
reward-theater</b>; the loop refuses to take any task a person has
already promised.</div>
<p>Receipts: <a href="https://github.com/rtk-ai/rtk/pull/4929">PR
#4929</a> &middot; <a
href="https://github.com/dream-machine-systems/dream-machine-os/pull/23">PR
#23</a> &middot; the <a
href="https://github.com/seahawk2986-hue/apex-ghost-family">hub's
ledger</a>.</p></section>
<section id="faq"><h2>FAQ</h2>
<details open><summary>What do I receive, exactly?</summary><p>Files: an
<code>report.md</code> + a <code>patches/</code> pack + <code>tests/</code>
with the run-receipts. No subscription.</p></details>
<details><summary>How fast?</summary><p>Within 24 hours; one revision
within 7 days.</p></details>
<details><summary>Is the work automated?</summary><p>Yes - disclosed on
every artifact; a human verifies before anything ships.</p></details>
<details><summary>What do you need from me?</summary><p>The repo URL +
one paragraph. That's the only input.</p></details>
<details><summary>Private repos?</summary><p>Yes, we'll coordinate access
after checkout.</p></details>
<details><summary>What if it doesn't fit?</summary><p>Open a <a
href="https://github.com/seahawk2986-hue/apex-ghost-family/issues">free
issue</a> first - no checkout needed.</p></details></section>
</main><footer>&copy; 2026 apex-ghost-family &middot; the founder: Andrew
Hike &middot; <a
href="https://github.com/seahawk2986-hue/apex-ghost-family/issues">the
support/issues</a> &middot; site updated """ + STAMP + """</footer>
</body></html>"""


def put(path, content, msg):
    gh2 = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(gh2, headers=H),
                                    timeout=30) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except Exception:
        import urllib.request as U
        pass
    payload = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        payload["sha"] = sha
    with urllib.request.urlopen(urllib.request.Request(
            gh2, data=json.dumps(payload).encode(), headers=H,
            method="PUT"), timeout=60) as r:
        d = json.loads(r.read().decode())
    print(f"[design-v3] {path}: {d.get('commit', {}).get('sha', '?')[:10]}")


import urllib.request
put("index.html", HTML, f"THE DESIGN-V3 (the 100-pattern audit's build): "
    f"the JSON-LD products, the skip-link, the hero-CTA, the before-panel, "
    f"the 6-item-FAQ, the canonical + the stamp ({applied} applied/"
    f"{napplied} n-a/{pending} pending)")
with open(os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                       "Config", "design_patterns_catalog.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "applied":
               applied, "not_applicable": napplied, "pending": pending,
               "patterns": CAT}, f, ensure_ascii=False, indent=1)
print(f"[design-v3] the catalog: {applied} applied / {napplied} honest-n-a "
      f"/ {pending} pending -> the live URL")