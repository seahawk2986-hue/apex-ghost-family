import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import PatchStep as PS
tok = PS.token()
st, issues = PS.api("/repos/rtk-ai/rtk/issues?state=open&per_page=40", tok)
for it in (issues if st == 200 else []):
    if "muse" in ((it.get("title", "") + (it.get("body") or "")).lower()):
        print("TITLE:", it.get("title"))
        print("NUMBER:", it.get("number"))
        print("LABELS:", [l.get("name") for l in it.get("labels", [])])
        print("----BODY----")
        print((it.get("body") or "")[:5500])
        break
else:
    print("not found")