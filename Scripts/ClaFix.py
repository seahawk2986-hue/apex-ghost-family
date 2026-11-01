import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
st, user = PS.api("/user", tok)
login = user.get("login", "?")
uid = user.get("id", 0)
noreply = f"{uid}+{login}@users.noreply.github.com"
print(f"the account: {login} (id {uid}) | the canonical commit email: "
      f"{noreply}")
# the global identity updated (the future commits CLA-clean)
subprocess.run(["git", "config", "--global", "user.name", login])
subprocess.run(["git", "config", "--global", "user.email", noreply])
# the workspace: amend the commit's author + force-push
wd = json.load(open(r"C:\Users\seaha\Apex-Adapter\pr_pipeline_state.json",
                    encoding="utf-8-sig"))["workspace"]
a = subprocess.run(["git", "commit", "--amend", "--no-edit",
                    "--reset-author", f"--author={login} <{noreply}>"],
                   cwd=wd, capture_output=True, text=True)
print("amend:", a.returncode, "author now:",
      subprocess.run(["git", "log", "-1", "--format=%an <%ae>"], cwd=wd,
                     capture_output=True, text=True).stdout.strip())
pf = subprocess.run(["git", "push", "-f", "-u", "origin", "apex-fix"],
                    cwd=wd, capture_output=True, text=True, timeout=120)
print(f"force-push: rc={pf.returncode} {(pf.stderr or '')[:70]}")
with open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Config"
          r"\AscentLedger.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": "upward",
                        "what": "CLA-email-fix (the commits now carry the "
                                "account's canonical noreply; the SIGN = "
                                "the founder's one click on the bot's "
                                "link)"}) + "\n")
print("NEXT (founder's one click): open the PR conversation and click "
      "'sign the CLA' (the bot's link) - it opens the CLA-assistant; "
      "sign with the " + login + " account; then the bot's 'recheck'.")