import json
import sys

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
REPOS = [("rtk-ai/rtk", 4929), ("dream-machine-systems/dream-machine-os", 23)]
for repo, no in REPOS:
    print("=" * 20, repo, f"PR #{no}")
    st, iss = PS.api(f"/repos/{repo}/issues/{no}", tok)
    if st != 200:
        print("  unreadable:", st)
        continue
    print(" state:", iss.get("state"), "| assigned:",
          [a.get("login") for a in iss.get("assignees", [])],
          "| labels:", [l.get("name") for l in iss.get("labels", [])])
    st2, cms = PS.api(f"/repos/{repo}/issues/{no}/comments?per_page=30", tok)
    for c in (cms if st2 == 200 else [])[-3:]:
        print(f"  -- {c['user']['login']} @ {c['created_at'][:16]}:")
        print("     " + (c.get("body") or "").replace("\n", " "
                      .replace("\n", " "))[:400])
    st3, checks = PS.api(f"/repos/{repo}/commits/{'apex'}?per_page=3", tok) if False \
        else (None, None)
    labels = [l.get("name") for l in iss.get("labels", [])]
print("done")