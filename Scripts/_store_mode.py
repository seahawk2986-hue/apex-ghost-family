"""READ THE STORE-MODE OFF THE LIVE SITE: the buy-links' domains tell
the truth (polar.sh = LIVE / sandbox.polar.sh = TEST)."""
import re
import urllib.request

b = urllib.request.urlopen(
    "https://seahawk2986-hue.github.io/apex-ghost-family/",
    timeout=25).read().decode("utf-8", "replace")
links = sorted(set(re.findall(r"https://[^\s\"'`<>]*polar[^\s\"'`<>]*", b)))
print(f"buy-links found: {len(links)}")
sand = live = 0
for l in links:
    tag = "SANDBOX(test)" if "sandbox" in l else "LIVE"
    if "sandbox" in l:
        sand += 1
    else:
        live += 1
    print(f"  [{tag}] {l[:95]}")
print(f"VERDICT: {live} live / {sand} sandbox")
if links and live:
    print("=> the checkouts = LIVE. The founders' $0s = zero SALES only; "
          "no go-live click needed (the store already accepts money).")
elif links and sand:
    print("=> the checkouts = SANDBOX. The go-live toggle = still needed "
          "(Settings -> complete business details -> Go live).")