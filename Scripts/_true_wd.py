import json
import os
import subprocess

s = json.load(open(r"C:\Users\seaha\Apex-Adapter\pr_pipeline_state.json",
                   encoding="utf-8-sig"))
wd = s["workspace"]
print("the REAL workspace:", wd)
print("exists:", os.path.isdir(wd))
if os.path.isdir(wd):
    print(subprocess.run(["git", "status", "--short"], cwd=wd,
                         capture_output=True, text=True).stdout[:300])
    print(subprocess.run(["git", "log", "--oneline", "-3"], cwd=wd,
                         capture_output=True, text=True).stdout)
    print(subprocess.run(["git", "config", "user.name"], cwd=wd,
                         capture_output=True, text=True).stdout
          or "(no local identity)")
    print("hooks/muse on disk:",
          os.path.isdir(os.path.join(wd, "hooks", "muse")) and
          os.listdir(os.path.join(wd, "hooks", "muse")))