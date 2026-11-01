"""OG-TAG-ONLY: the index.html's og:image-meta add (the fetch-edit-put,
the idempotent: the og-tag-exists = the skip-honest); the = the = = = =."""
import base64
import json
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

H = {"Authorization": "Bearer " + PS.token(),
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json", "User-Agent": "apex-og/2.0"}
REPO = "seahawk2986-hue/apex-ghost-family"
gh2 = f"https://api.github.com/repos/{REPO}/contents/index.html"
d = json.loads(urllib.request.urlopen(
    urllib.request.Request(gh2, headers=H), timeout=30).read())
b = base64.b64decode(d["content"]).decode()
if "og:image" in b:
    print("[og] the og:image-meta ALREADY-in (the idempotent-honest)")
else:
    b = b.replace('<meta property="og:type" content="website">',
                  '<meta property="og:type" content="website">\n'
                  '<meta property="og:image" content='
                  '"https://seahawk2986-hue.github.io/apex-ghost-family/'
                  'og_banner.png">'
                  '<meta property="og:image:width" content="1200">'
                  '<meta property="og:image:height" content="630">')
    payload = {"message": "the og:image-meta (the banner = the linked)",
               "content": base64.b64encode(b.encode()).decode(),
               "sha": d["sha"]}
    with urllib.request.urlopen(urllib.request.Request(
            gh2, data=json.dumps(payload).encode(), headers=H,
            method="PUT"), timeout=60) as r:
        print("[og] index.html: the og:image-meta = COMMITTED",
              json.loads(r.read().decode()).get("commit", {}).get("sha", "?")[:10])