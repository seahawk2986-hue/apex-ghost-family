"""the storefront: the 3 live checkout-links = the BUY buttons."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\jobs_page.html"
h = open(P, encoding="utf-8").read()
a = h.find("<h2>SERVICES")
if a == -1:
    a = 200
buttons = ('<div style="margin:10px 0">'
           '<a href="https://polar.sh/checkout/polar_c_gDfAWTkBJWAriu609ZFeNev8JXeQ2srCgsMd" '
           'target="_blank" style="display:inline-block;background:var(--green);color:#0d1117;'
           'padding:8px 14px;border-radius:6px;font-weight:600;margin-right:8px;text-decoration:none">'
           'REPO TRIAGE &amp; PATCH — $75</a>'
           '<a href="https://polar.sh/checkout/polar_c_4mQGCcebZ3uKfnnO1ht9lDyREsw8e0jVT9on" '
           'target="_blank" style="display:inline-block;background:var(--blue);color:#0d1117;'
           'padding:8px 14px;border-radius:6px;font-weight:600;margin-right:8px;text-decoration:none">'
           'CODE FIX PACK — $150</a>'
           '<a href="https://polar.sh/checkout/polar_c_1mV2kqe9qKISW3F17vOasbGkIHkBtpz4l5fH" '
           'target="_blank" style="display:inline-block;background:var(--gold);color:#0d1117;'
           'padding:8px 14px;border-radius:6px;font-weight:600;text-decoration:none">'
           'DATA/ML PIPELINE PACK — $200</a></div>')
if "polar_c_" not in h:
    h = h[:a] + buttons + h[a:]
    open(P, "w", encoding="utf-8").write(h)
    print("[storefront]: the 3 BUY buttons = LIVE")
else:
    print("[storefront]: the buttons already in")
try:
    import requests
    r = requests.get('https://desktop-6t3u1lh.tail929a0b.ts.net/', timeout=20,
                     headers={"User-Agent": "Apex-Adapter/2.0"})
    print("[public page]:", r.status_code, "| buy-buttons visible:", "polar_c_" in r.text)
except Exception as e:
    print("[public check]:", type(e).__name__, str(e)[:60])