"""SkillLibrary - Apex's cloud-sourced, vetted skill library.

Harvest: GitHub public repos (permissive license) -> vet (compile, bandit, import
allowlist, size caps) -> register with SHA256 + provenance -> intent-indexed.
CLI: search "keywords" | list | show NAME | stats
Everything offline after harvest; no keys; $0; bounded by HostGuard disk rules.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LIB_PATH = os.path.join(REPO, "Config", "SkillLibrary.json")
STAGE = os.path.join(ADAPTER := r"C:\Users\seaha\Apex-Adapter", "skill_stage")
LICENSES = {
    "TheAlgorithms/Python": "MIT (TheAlgorithms/Python)",
    "geekcomputers/Python": "MIT (geekcomputers/Python)",
}
BANNED_IMPORTS = ("socket", "ftplib", "telnetlib", "paramiko", "smtplib",
                  "urllib.request", "http.client", "requests", "ctypes",
                  "subprocess", "multiprocessing", "webbrowser", "sqlite3")
MAX_LINES = 400
MAX_FILES_PER_SOURCE = 40


def sha_text(t):
    return hashlib.sha256(t.encode("utf-8", errors="ignore")).hexdigest()


def gh_api(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "ApexSkillHarvester/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load():
    try:
        return json.load(open(LIB_PATH, encoding="utf-8-sig"))
    except Exception:
        return {"skills": [], "sources": [], "built": time.strftime("%Y-%m-%d %H:%M:%S")}


def save(lib):
    lib["built"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LIB_PATH, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=1, ensure_ascii=False)


def vet(path):
    """Return (ok, reason). Cutting-edge vetting: compile + bandit + import gate."""
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return False, "unreadable"
    if len(src.splitlines()) < 3:
        return False, "too small"
    if len(src.splitlines()) > MAX_LINES:
        return False, "too large"
    banned = [b for b in BANNED_IMPORTS
              if re.search(r"^\s*(import|from)\s+" + re.escape(b.split('.')[0]), src, re.M)]
    if banned:
        return False, "banned import: " + banned[0]
    for pat in (r"eval\(", r"exec\(", r"__import__", r"open\(['\"]?C:", r"\binput\("):
        if re.search(pat, src):
            return False, "risky pattern: " + pat
    tmp = os.path.join(STAGE, os.path.basename(path))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run([sys_exec(), "-c",
                        "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)",
                        tmp], capture_output=True, timeout=30)
    if r.returncode != 0:
        return False, "compile failed"
    b = subprocess.run([sys_exec(), "-m", "bandit", "-q", "-f", "json", tmp],
                       capture_output=True, text=True, timeout=60)
    try:
        report = json.loads(b.stdout or "{}")
        totals = (report.get("metrics", {}) or {}).get("_totals", {})
        if totals.get("severity_high"):
            return False, "bandit HIGH-severity finding"
        medium = totals.get("severity_medium")
        ok = True
        why = "verified" + (f" (note: {medium} medium findings)" if medium else "")
    except Exception as e:
        return False, "bandit parse failed: " + str(e)[:60]
    return ok, why




def _library_reward(points, text, milestone=False):
    import uuid as _u
    try:
        rw = json.load(open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                            r"\Config\GymRewards.json", encoding="utf-8-sig"))
    except Exception:
        rw = {"points": 0}
    rw["library_points"] = rw.get("library_points", 0) + points
    rw["points"] = rw.get("points", 0) + points
    with open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
              r"\Config\GymRewards.json", "w", encoding="utf-8") as f:
        json.dump(rw, f, indent=1)
    row = {"id": _u.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": "success", "text": text[:500],
           "meta": {"library_points": points, "total": rw["points"]}, "imp": 0.7}
    ep = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\memory_episodic.jsonl"
    with open(ep, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")
    if milestone:
        try:
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                                     r"\Scripts\ApexSpeak.ps1", "-Message", text],
                           timeout=60, capture_output=True)
        except Exception:
            pass


def sys_exec():
    return os.path.join(REPO, "apex_venv", "Scripts", "python.exe")


def harvest(repo, per_source):
    """Fetch file tree via GitHub API; select py files; vet; stage."""
    os.makedirs(STAGE, exist_ok=True)
    try:
        info = gh_api(f"https://api.github.com/repos/{repo}")
        branch = info.get("default_branch", "main")
    except Exception:
        branch = "main"
    tree = gh_api(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    picked = 0
    for t in tree.get("tree", []):
        if picked >= per_source:
            break
        p = t.get("path", "")
        if any((x.get("source_file") == p and x.get("source_repo") == repo) for x in load()["skills"]):
            continue
        if not p.endswith(".py") or "/" not in p:
            continue
        if any(x in p.lower() for x in ("test", "setup", "example_", "game")):
            continue
        if (t.get("size") or 0) > 12000:
            continue
        raw = f"https://raw.githubusercontent.com/{repo}/{branch}/{p}"
        try:
            import urllib.request
            req = urllib.request.Request(raw, headers={"User-Agent": "ApexSkillHarvester/1.0"})
            content = urllib.request.urlopen(req, timeout=30).read().decode(
                "utf-8", errors="ignore")
        except Exception:
            continue
        if len(content.splitlines()) < 3:
            continue
        tmpname = f"{repo.replace('/', '_')}__{p.replace('/', '__')}"
        tmp = os.path.join(STAGE, tmpname)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        ok, why = vet(tmp)
        print(("KEEP " if ok else "SKIP ") + p + " (" + why + ")", flush=True)
        if ok:
            lib = load()
            doc = {"skill": os.path.basename(p)[:-3],
                   "source_file": p, "source_repo": repo,
                   "license": LICENSES.get(repo, "check repo"),
                   "sha256": sha_text(content), "lines": len(content.splitlines()),
                   "first_line": content.splitlines()[0][:120],
                   "imports": sorted(set(re.findall(r"^\s*import\s+(\w+)", content, re.M)))[:8],
                   "registered": time.strftime("%Y-%m-%d %H:%M:%S")}
            lib["skills"].append(doc)
            save(lib)
            picked += 1
            _library_reward(15, "HARVEST: registered verified skill " + doc["skill"]
                            + " from " + repo + ".", milestone=(picked % 10 == 0))


def harvest_all(per_source=MAX_FILES_PER_SOURCE):
    lib = load()
    for repo in LICENSES:
        print("harvest:", repo, "(dedup resumes/repeats safely)", flush=True)
        harvest(repo, per_source)
    lib = load()
    print("LIBRARY:", len(lib["skills"]), "skills registered")


def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("harvest", "list", "search", "show", "stats", "raw"))
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--minutes", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "harvest":
        harvest_all()
    elif a.cmd == "list":
        _library_reward(2, "Library consult (list) rewarded.")
        for s in load()["skills"]:
            print(f"{s['skill']:40s} [{s['source_repo'].split('/')[0]}] {s['summary'] if s.get('summary') else s['source_file'][:50]}")
    elif a.cmd == "search":
        words = set(re.findall(r"[a-z]{3,}", (a.query or "").lower()))
        for s in load()["skills"]:
            hay = (s["skill"] + " " + s["source_file"] + " " + " ".join(s.get("imports", []))).lower()
            if len(words & set(re.findall(r"[a-z]{3,}", hay))) >= 1:
                _library_reward(4, "Library consult (search " + repr(a.query) + ") rewarded.")
                print(s["skill"], "|", s["source_file"], "| sha:", s["sha256"][:12])
    elif a.cmd == "stats":
        lib = load()
        byc = {}
        for s in lib["skills"]:
            first = (s.get("imports") or ["core"])[0]
            byc[first] = byc.get(first, 0) + 1
        print(json.dumps({"skills": len(lib["skills"]), "categories": byc}, indent=1))
        _library_reward(3, "Library stats consult rewarded.")
    elif a.cmd == "raw":
        # print the actual source of the first matching skill (Apex reads it)
        for s in load()["skills"]:
            if a.query.lower() in s["skill"].lower() or a.query.lower() in s["source_file"].lower():
                print(open(os.path.join(STAGE, s["source_repo"].replace("/", "_") + "__" +
                                         s["source_file"].replace("/", "__")),
                           encoding="utf-8", errors="ignore").read())
                return


if __name__ == "__main__":
    cli()