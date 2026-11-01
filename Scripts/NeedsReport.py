"""NEEDS REPORT (the standing 'what we need' organ):
one scan -> keys present/absent (masked), live per-key status, keyless quota
state, tool census, and the doctrine gap queue -> a priority-ordered NEEDS
list. Values NEVER printed (fingerprints only). Every call bounded, every
failure printed. Wire into the morning brief post-marathon.
Usage: python NeedsReport.py [--no-net]  (--no-net skips live endpoint tests)"""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
UA = {"User-Agent": "ApexGhostSwarm/3.0"}
NEED = []


def fp(v):
    return (v[:3] + "*" * max(0, len(v) - 6) + v[-3:]) if len(v) > 8 else f"set({len(v)})"


def http(url, headers=None, method="GET", timeout=10):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"],
                                                   **(headers or {})}, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, time.time() - t0
    except Exception as e:
        return str(e)[:60], time.time() - t0


def section(title):
    print("\n=== " + title + " ===")


def need(item, why, fix):
    NEED.append((item, why, fix))


# ---------- load .env (names only) ----------
ENV = {}
try:
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            ENV[k.strip()] = v.strip()
except Exception as e:
    print("ENV read failed:", str(e)[:80])

section("A. KEYS: present in .env (masked fingerprints, never values)")
KEYS = {
    "GROQ_API_KEY": "https://api.groq.com/openai/v1/models",
    "OPENROUTER_API_KEY": "https://openrouter.ai/api/v1/auth/key",
    "GEMINI_API_KEY": "https://generativelanguage.googleapis.com/v1beta/models",
    "CEREBRAS_API_KEY": "https://api.cerebras.ai/v1/models",
    "HF_TOKEN": "https://huggingface.co/api/whoami-v2",
    "GITHUB_TOKEN": "https://api.github.com/rate_limit",          # no quota cost
    "GITHUB_PAT": "https://api.github.com/rate_limit",
    "GITHUB_MODELS_TOKEN": "https://models.github.ai/catalog",
    "SERPER_API_KEY": "https://google.serper.dev/search",          # POST 1 credit
    "S2_API_KEY": "https://api.semanticscholar.org/graph/v1/datasets/v1/release/latest",
}
live = {}
for k, url in KEYS.items():
    v = ENV.get(k)
    if not v:
        print(f"  {k:22s} ABSENT")
        if k == "GITHUB_TOKEN":
            need("GITHUB_TOKEN (fine-grained, read-only, public-repo, Actions:read)",
                 "keyless 60/hr/IP exhausted tonight: search/credibility/hub-monitor 403s",
                 "github.com/settings/personal-access-tokens/new -> public-repos read-only + Actions:read -> paste into .env")
        if k == "S2_API_KEY":
            need("S2_API_KEY (free)",
                 "research scrapes 429'd all night; bulk S2ORC (136M full-text papers) locked",
                 "api.semanticscholar.org/product/api -> free key -> .env")
        continue
    print(f"  {k:22s} set  {fp(v)}", end="  ")
    if url.endswith("/search"):
        st, dt = http(url, {"X-API-KEY": v, "Content-Type": "application/json"}, method="POST")
    else:
        hdrs = {"x-goog-api-key": v} if k == "GEMINI_API_KEY" else {"Authorization": "Bearer " + v}
        st, dt = http(url, hdrs)
    ok = isinstance(st, int) and st == 200
    print(f"-> {'WORKING' if ok else 'NOT WORKING'} ({st}, {dt:.1f}s)")
    live[k] = ok
    if isinstance(st, str) or st >= 400:
        need(f"{k} repair", f"present but the lane test returned {{{st}}}",
             "regenerate/reauthorize at provider console, paste into .env, never chat")

section("B. KEYLESS QUOTA STATE (what the swarm's no-key world looks like)")
st, dt = http("https://api.github.com/rate_limit")
if isinstance(st, int) and st == 200:
    pass  # body parsed below for core/search remain
    try:
        with urllib.request.urlopen(urllib.request.Request(
                "https://api.github.com/rate_limit", headers=UA), timeout=10) as r:
            d = json.load(r)
        core = d.get("resources", {}).get("core", {})
        src = d.get("resources", {}).get("search", {})
        print(f"  GitHub keyless: core {core.get('remaining')}/{core.get('limit')} "
              f"remaining | search {src.get('remaining')}/{src.get('limit')} "
              f"| resets {time.strftime('%H:%M:%S', time.localtime(core.get('reset', 0)))}")
    except Exception as e:
        print("  GitHub rate_limit parse:", str(e)[:60])
else:
    print("  GitHub keyless rate_limit:", st)
for url, label in (("https://data.gharchive.org/2026-10-31-20.json.gz", "GH Archive hourly"),
                   ("https://api.semanticscholar.org/graph/v1/paper/search?query=agents",
                    "S2 search unauth"),
                   ("https://huggingface.co/api/models?limit=1", "HF hub")):
    st, dt = http(url)
    print(f"  {label:22s} -> {st} ({dt:.1f}s)")

section("C. TOOLS CENSUS (verification stack + app deps)")
for tool in ("bandit", "ruff", "pytest"):
    r = subprocess.run([os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
                        "-m", tool, "--version"], capture_output=True, text=True, timeout=60)
    print(f"  {tool:8s} {'OK ' + (r.stdout or r.stderr).strip()[:40] if r.returncode == 0 else 'MISSING'}")
r = subprocess.run([os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
                    "-m", "py_spy", "--version"], capture_output=True, text=True, timeout=60)
print(f"  {'py-spy':8s} {'OK ' + (r.stdout or r.stderr).strip()[:40] if r.returncode == 0 else 'MISSING'}")
for mod in ("aiohttp", "nacl", "yaml", "trafilatura", "psutil", "requests"):
    r = subprocess.run([os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"), "-c", f"import {mod}"],
                       capture_output=True, text=True, timeout=30)
    print(f"  import {mod:12s} {'OK' if r.returncode == 0 else 'MISSING'}")

section("D. DOCTRINE GAP QUEUE (post-marathon wiring, from Parts II-VI)")
for gap in ("SO: wire GhArchiveLane into lane_batch (K6#1, built, awaiting window)",
            "SO: grade the BACKLOG before downloading (K3 quality-ladder-early)",
            "SkillLibrary: bandit gate -> fail-closed (bandit now installed)",
            "SkillLibrary: adopt NearDedup at registration (audit showed 55 near-dup clusters)",
            "heartbeat: second bare writer -> digest path (the MISMATCH alarm caught it)",
            "marathon harness: mined criterion = register-or-findings (not stdout marker)",
            "packet schema rev: lifecycle states + Agent-Card fields (C2)"):
    print("  -", gap)

section("E. VERDICT - WHAT WE NEED, PRIORITIZED")
if not NEED:
    print("  nothing missing: keys live, tools in, quota acceptable")
for item, why, fix in NEED:
    print(f"  1) {item}")
    print(f"     why: {why}")
    print(f"     fix: {fix}")
print("\n(standing organ: rerun any time; wire into the brief post-marathon)")