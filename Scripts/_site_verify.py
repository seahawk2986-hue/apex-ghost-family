"""THE SITE-V3 VERIFY: the build's settle -> the live-markers."""
import time
import urllib.request

for attempt in range(3):
    time.sleep(60)
    try:
        r = urllib.request.urlopen(
            "https://seahawk2986-hue.github.io/apex-ghost-family/",
            timeout=30)
        b = r.read().decode("utf-8", "replace")
        print(f"[site-v3] HTTP {r.status} | {len(b)} bytes | "
              f"schema.org-JSON: {'schema.org' in b} | skip-link: "
              f"{'Skip to content' in b} | buy-links: "
              f"{b.count('buy.polar.sh')}")
        if "schema.org" in b:
            print("[site-v3] VERDICT: THE 100-PATTERN V3 IS LIVE")
            break
    except Exception as e:
        print(f"[site-v3] the attempt {attempt + 1}: {str(e)[:70]}")