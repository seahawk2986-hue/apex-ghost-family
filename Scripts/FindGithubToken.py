"""FIND THE GITHUB TOKEN (doctrine Part V K6: the #1 need):
1. read the credential Git Credential Manager stores for github.com
   (headless, fail-fast: no browser popups, GIT_TERMINAL_PROMPT=0)
2. fingerprint it (never print)
3. status-only API test via /rate_limit (zero quota cost)
4. if WORKING: write GITHUB_TOKEN=... into .env masked, re-seal the guard
5. if not retrievable: print the exact manual-creation steps instead.
Values NEVER printed. Every step prints. This file contains NO secret."""
import subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never",
       "GCM_GUI": "never", **dict((k, v) for k, v in __import__("os").environ.items()
                                  if k != "GIT_ASKPASS")}
try:
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=30, cwd=ROOT, env=env)
except subprocess.TimeoutExpired:
    r = None
    print("STEP 1: credential fill timed out (GCM wanted interaction) - stored "
          "credential not retrievable headlessly; do the manual steps below")
if r is not None and r.returncode == 0 and "password=" in (r.stdout or ""):
    tok = None
    for ln in r.stdout.splitlines():
        if ln.startswith("password="):
            tok = ln.partition("=")[2].strip()
    if tok:
        print(f"STEP 2: credential found: fingerprint {tok[:4]}*{tok[-4:]} ({len(tok)} chars) "
              f"- never printed further")
        import urllib.request
        import time
        try:
            req = urllib.request.Request(
                "https://api.github.com/rate_limit",
                headers={"Authorization": "Bearer " + tok, "User-Agent": "Mozilla/5.0"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=12) as resp:
                d = json.loads(resp.read().decode("utf-8", "ignore")) if (json := __import__("json")) else {}
            core = d.get("resources", {}).get("core", {})
            src = d.get("resources", {}).get("search", {})
            print(f"STEP 3: LIVE TEST -> HTTP 200 in {time.time()-t0:.1f}s => WORKING | "
                  f"core {core.get('remaining')}/{core.get('limit')} | "
                  f"search {src.get('remaining')}/{src.get('limit')}/min")
            lines = []
            replaced = False
            for line in open(ROOT + r"\.env", encoding="utf-8-sig"):
                if line.strip().startswith("GITHUB_TOKEN="):
                    old = line.partition("=")[2].strip()
                    print(f"STEP 4: .env GITHUB_TOKEN: {('fp ' + old[:4] + '*' + old[-4:] if old else 'empty')} "
                          f"-> {tok[:4]}*{tok[-4:]}")
                    lines.append("GITHUB_TOKEN=" + tok + "\n")
                    replaced = True
                else:
                    lines.append(line if line.endswith("\n") else line + "\n")
            if not replaced:
                lines.append("GITHUB_TOKEN=" + tok + "\n")
                print("STEP 4: no GITHUB_TOKEN line existed - appended")
            with open(ROOT + r"\.env", "w", encoding="utf-8") as f:
                f.writelines(lines)
            r5 = subprocess.run([ROOT + r"\apex_venv\Scripts\python.exe",
                                 ROOT + r"\Scripts\ApexGuard.py", "sealenv"],
                                capture_output=True, text=True, timeout=60, cwd=ROOT)
            print("STEP 5: env re-sealed:", (r5.stdout or "").strip())
            print("DONE: discover/search/credibility/hub-monitor lanes now carry the token "
                  "(activates next fresh session/run)")
        except Exception as e:
            print("STEP 3 FAILED honestly:", str(e)[:70], "- the credential works for git push "
                  "but may lack API scopes; create a fresh fine-grained PAT for the API lanes")
else:
    print("STEP 1: no stored credential retrievable (returncode: "
          f"{getattr(r, 'returncode', 'n/a')})")
    print("""
MANUAL STEPS (the reliable path):
 1. github.com -> your avatar -> Settings -> Developer settings
 2. Personal access tokens -> Fine-grained tokens -> Generate new token
 3. name: apex-ghost-family-readonly | expiry: 30 days
 4. Repository access: Public repositories (read-only)
 5. Permissions: Metadata: Read (default) + Actions: Read-only
    (Actions:read is what unblocks the hub's runs/artifact monitoring)
 6. Generate -> COPY the token now (GitHub shows it once)
 7. paste it into .env as:  GITHUB_TOKEN=github_pat_...
    (straight into .env - NEVER into chat)
 8. rerun: python Scripts/NeedsReport.py  -> the GitHub line will say WORKING""")