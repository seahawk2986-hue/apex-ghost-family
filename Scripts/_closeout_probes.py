"""THE DAY'S CLOSE-OUT PROBES: the 3 quenched free-lanes + the PR-pipeline
readiness - all $0, all honest."""
import json
import os
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")
envfile = os.path.join(ROOT, ".env")
env = {}
for ln in open(envfile, encoding="utf-8-sig"):
    ln = ln.strip()
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()

print("== the free-lane re-probe ==")
# 1. groq (the chat-voice = the critical one)
try:
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({"model": "openai/gpt-oss-120b",
                         "messages": [{"role": "user", "content": "ping"}],
                         "max_tokens": 5}).encode(),
        headers={"Authorization": f"Bearer {env.get('GROQ_API_KEY','')}",
                 "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=25)
    print(f"  groq: LIVE (the 120b serving, {r.status})")
except Exception as e:
    print(f"  groq: {str(e)[:70]}")
# 2. gemini
try:
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-flash-latest:generateContent?key={env.get('GEMINI_API_KEY','')}",
        data=json.dumps({"contents": [{"parts": [{"text": "ping"}]}]}).encode(),
        headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=25)
    print(f"  gemini-flash: LIVE again (the cooldown = over)")
except Exception as e:
    print(f"  gemini-flash: still {str(e)[12:60]}")
# 3. openrouter
try:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps({"model": "openai/gpt-oss-120b:free",
                         "messages": [{"role": "user", "content": "ping"}]}).encode(),
        headers={"Authorization": f"Bearer {env.get('OPENROUTER_API_KEY','')}",
                 "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=25)
    print(f"  openrouter: LIVE again")
except Exception as e:
    print(f"  openrouter: still {str(e)[12:60]}")

print("== the PR-pipeline readiness ==")
for f in (".github/workflows/apex-prlane.yml", "Scripts/_runner_prfile.py",
          "Config/pr_pipeline_state.json"):
    fp = os.path.join(ROOT, f)
    print(f"  {f}: {'EXISTS' if os.path.exists(fp) else 'MISSING'}")
try:
    sys_p = os.path.join(ROOT, "Scripts")
    import sys as _s
    _s.path.insert(0, sys_p)
    import PatchStep as PS
    H = {"Authorization": "Bearer " + PS.token(),
         "Accept": "application/vnd.github+json"}
    r = urllib.request.urlopen(urllib.request.Request(
        "https://api.github.com/repos/seahawk2986-hue/apex-ghost-family"
        "/actions/workflows/apex-prlane.yml/runs?per_page=1", headers=H),
        timeout=25)
    x = json.loads(r.read().decode()).get("workflow_runs", [{}])[0]
    print(f"  the prlane last run: {x.get('created_at')} -> "
          f"{x.get('status')}/{x.get('conclusion')}")
except Exception as e:
    print(f"  the prlane read honest: {str(e)[:60]}")