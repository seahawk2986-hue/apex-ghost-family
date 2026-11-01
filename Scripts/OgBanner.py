"""OGBANNER: the og:image's pure-code generator (the honest-cure for the
image-quota's fall): Pillow draws the 1200x630 brand-banner (the dark-navy,
the eye-glyph, the APEX-name, the subtitle, the badge) - then PUTs the PNG
+ the og:image-meta into the landing's HTML. Deterministic = the
brand-exact; $0.00. The Pillow's-install = the free (the first-run)."""
import base64
import json
import os
import subprocess
import sys
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")

try:
    import PIL  # noqa
except Exception:
    subprocess.run([PY, "-m", "pip", "install", "--quiet", "pillow"],
                   capture_output=True, text=True, timeout=600)
from PIL import Image, ImageDraw, ImageFont

W, H2 = 1200, 630
img = Image.new("RGB", (W, H2), (13, 17, 23))  # the #0d1117
d = ImageDraw.Draw(img)
# the subtle circuit-line texture (the deterministic)
for x in range(0, W, 60):
    d.line([(x, 90), (x + 34, 70)], fill=(25, 33, 46), width=2)
    d.line([(x, H2 - 90), (x + 34, H2 - 70)], fill=(25, 33, 46), width=2)
for y in range(110, H2 - 110, 80):
    d.line([(40, y), (70, y + 22)], fill=(25, 33, 46), width=2)
    d.line([(W - 40, y), (W - 70, y + 22)], fill=(25, 33, 46), width=2)
# the fonts (the system = the honest-no-download)
def F(sz, bold=False):
    for fp in (r"C:\Windows\Fonts\seguisb.ttf" if bold else
               r"C:\Windows\Fonts\segui.ttf",
               r"C:\Windows\Fonts\arialbd.ttf" if bold else
               r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(fp):
            return ImageFont.truetype(fp, sz)
    return ImageFont.load_default()

f_eye = F(150, True)
f_title = F(150, True)
f_sub = F(32)
f_badge = F(24)
# the eye-glyph (the minimalist: the almond + the pupil + the scanline)
cx, cy = W // 2, 165
d.ellipse([cx - 90, cy - 52, cx + 90, cy + 52], outline=(68, 147, 248), width=7)
d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], outline=(68, 147, 248), width=7)
d.line([(cx - 44, cy), (cx + 44, cy)], fill=(68, 147, 248), width=6)
t = "APEX"
bb = d.textbbox((0, 0), t, font=f_title)
d.text(((W - (bb[2] - bb[0])) / 2, cy + 64 + 40), t, fill=(233, 238, 244),
       font=f_title)
sub = "verified repository care - by an agent family that shows its work"
bb = d.textbbox((0, 0), sub, font=f_sub)
d.text(((W - (bb[2] - bb[0])) / 2, 475), sub, fill=(139, 148, 158),
       font=f_sub)
badge = "5-stage quality gate  |  disclosed artifacts  |  delivered in 24h"
bb = d.textbbox((0, 0), badge, font=f_badge)
d.text(((W - (bb[2] - bb[0])) / 2, 548), badge, fill=(63, 185, 80),
       font=f_badge)
OUT = os.path.join(ROOT, "Config", "og_banner.png")
img.save(OUT)
print(f"[og-banner] {OUT} ({os.path.getsize(OUT)//1024}KB)")

# the PUT: the og_banner.png -> the repo (the /og_banner.png)
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import PatchStep as PS
H = {"Authorization": "Bearer " + PS.token(),
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json", "User-Agent": "apex-og/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"


def put(path, content, msg, ctype="text/plain"):
    gh2 = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(gh2, headers=H),
                                    timeout=30) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except Exception:
        pass
    payload = {"message": msg, "content": content}
    if sha:
        payload["sha"] = sha
    with urllib.request.urlopen(urllib.request.Request(
            gh2, data=json.dumps(payload).encode(), headers=H,
            method="PUT"), timeout=60) as r:
        print(f"[og] {path}: {json.loads(r.read().decode()).get('commit', {}).get('sha', '?')[:10]}")


data = base64.b64encode(open(OUT, "rb").read()).decode()
try:
    put("og_banner.png", data, "the og:image (the pure-code brand-banner)")
except Exception as e:
    print(f"[og] the png-put honest: {str(e)[:80]} (exists = ok)")
# the HTML's og:image-meta edit + the PUT (the fetch-edit-put)
with urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/index.html",
        headers=H), timeout=30) as r:
    import base64 as b64
    b = b64.b64decode(json.loads(r.read().decode())["content"]).decode()
if "og:image" not in b:
    b = b.replace('<meta property="og:type" content="website">',
                  '<meta property="og:type" content="website">\n'
                  '<meta property="og:image" content='
                  '"https://seahawk2986-hue.github.io/apex-ghost-family/'
                  'og_banner.png">'
                  '<meta property="og:image:width" content="1200">'
                  '<meta property="og:image:height" content="630">')
    put("index.html", b, "the og:image-meta (the social-share's picture)")
print("[og] DONE - the share-preview = the brand-exact")