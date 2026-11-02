"""The Polar store: verify + plant the buy-link into the storefront."""
import io
import sys

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
for url in ("https://polar.sh/apex-ghost-family-ai",
            "https://polar.sh/apex-ghost-family-ai/portal"):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Apex-Adapter/2.0"})
        print("[", r.status_code, "]", url, "| len:", len(r.text),
              "| 'apex-ghost' in page:", "apex-ghost" in r.text.lower())
    except Exception as e:
        print("[FAIL]", url, type(e).__name__, str(e)[:60])

P = r"C:\Users\seaha\Apex-Adapter\jobs_page.html"
h = open(P, encoding="utf-8").read()
a = h.find("<h2>CONTACT</h2>")
assert a != -1, "contact section gone"
store = ('<div class="kv" style="margin-top:8px">'
         '<a href="https://polar.sh/apex-ghost-family-ai" target="_blank" '
         'style="color:var(--gold)">BUY NOW - the live store: '
         'Data/ML Pipeline Pack $200 - Code Fix Pack $150 - Repository Triage '
         '&amp; Patch $75 (secure checkout by Polar)</a></div>')
if "polar.sh/apex-ghost-family-ai" not in h:
    h = h[:a] + store + h[a:]
    open(P, "w", encoding="utf-8").write(h)
    print("[storefront]: the buy-link planted")
else:
    print("[storefront]: the link already present")