import subprocess, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
for path in ("Scripts/FamilyKeys.py", "Config/apex_api.key", "adapter_token.txt"):
    r = subprocess.run(["git", "show", "0ec0828:" + path], capture_output=True, text=True)
    blob = r.stdout if r.returncode == 0 else ""
    if not blob:
        print(path, "-> not in the founding commit")
        continue
    lines = blob.count("\n") + 1
    assigns = [ln.split("=", 1)[0].strip() for ln in blob.splitlines()
               if "=" in ln and not ln.strip().startswith("#") and len(ln.split("=", 1)[1].strip().strip("\"").strip("'")) >= 12]
    longish = [s for s in re.findall(r"[A-Za-z0-9_\-\.]{25,}", blob) if not s.startswith(("def ", "import "))]
    tokish = bool(re.search(r"(tsat|tskey|ghp_|github_pat_|sk-|polar_|Bearer )", blob))
    print(path, "-> lines:", lines, "| 12+char assign names:", assigns[:8],
          "| token-marker:", tokish, "| longest-string lens:", sorted(set(len(s) for s in longish), reverse=True)[:3])
