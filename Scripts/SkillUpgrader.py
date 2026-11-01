"""SKILL UPGRADER (Part VIII W1 Voyager-shaping): text skills become
EXECUTABLE, VERIFIED, COMPILING records - the store compounds like Voyager's
library instead of accumulating text. For the top candidates (by GradeEarly
score or store order), it fetches the source ONCE via codeload tarball, runs
py_compile in a temp dir (verified-or-unclaimed), and annotates the record:
  executable: true/false, compiles: bool, verified_at.
Writes Config/curriculum.json - the AUTOMATIC CURRICULUM: the verified,
executable skills ranked, ready for retrieval by future runs.
Hardware: stdlib, bounded (top-N, 1 fetch each, 30s compile), RAM-gated."""
import gzip
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
STORE = os.path.join(ROOT, "Config", "SkillLibrary.json")
CURR = os.path.join(ROOT, "Config", "curriculum.json")


def ram_free():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def fetch_file(repo, path_part, cap=60000):
    """One codeload fetch per repo (cached per run): returns dict file->content.
    Branch fallback (the live 404 lesson: real repos 404 on refs/heads/HEAD) -
    try HEAD, then the plain default-branch tarball, then master, then main."""
    for suffix in ("refs/heads/HEAD", "", "refs/heads/master", "refs/heads/main"):
        try:
            url = f"https://codeload.github.com/{repo}/tar.gz"
            if suffix:
                url += "/" + suffix
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
            out = {}
            base = path_part.split("/", 1)[0]
            for m0 in tf.getmembers():
                if m0.isfile() and "/" in m0.name:
                    rel = m0.name.split("/", 1)[1]
                    if rel == path_part or (rel.startswith(base + "/") and len(out) < 8):
                        try:
                            out[rel] = tf.extractfile(m0).read().decode("utf-8", "ignore")[:cap]
                        except Exception:
                            pass
            if out:
                return out
        except Exception as e:
            last = str(e)[:60]
            continue
    print(f"[upgrader] fetch {repo} exhausted all branches ({last})")
    return {}


def compiles(src):
    try:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "cand.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(src)
            r = subprocess.run([sys.executable, "-c",
                                "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)",
                                p], capture_output=True, timeout=30)
            return r.returncode == 0
    except Exception:
        return False


def run(top_n=10):
    if ram_free() < 2.2:
        print("[upgrader] RAM below 2.2GB - skipped honestly")
        return None
    try:
        lib = json.load(open(STORE, encoding="utf-8-sig"))["skills"]
    except Exception as e:
        print("[upgrader] store unreadable:", str(e)[:60])
        return None
    try:
        grades = json.load(open(ROOT + r"\Config\backlog_grades.json",
                                encoding="utf-8-sig")).get("rows", [])
        prio = {r0["repo"]: r0["score"] for r0 in grades}
    except Exception:
        prio = {}
    ranked = sorted(lib, key=lambda s: -float(prio.get(s.get("source_repo", ""), 0)))
    n = 0
    curriculum = []
    cache = {}
    for s in ranked:
        if n >= top_n:
            break
        if s.get("executable_verified"):
            continue
        repo, path_part = s.get("source_repo", ""), s.get("source_file", "")
        if not repo or not path_part or repo in ("?", "None"):
            continue
        files = cache.get(repo) or fetch_file(repo, path_part)
        cache[repo] = files or cache.get(repo, {})
        src = files.get(path_part)
        ok = compiles(src) if src else False
        s["executable_verified"] = bool(src)
        s["compiles"] = ok
        s["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[upgrader] {s.get('skill', '?')[:44]} <- {repo[:32]}: "
              f"fetched={bool(src)} compiles={ok}")
        try:
            import RuntimeReceipt as _rr
            row = _rr._receipt(f"upgrader:{str(s.get('skill', '?'))[:36]}",
                               bool(ok), 0.0,
                               f"compile-verify (bounded subprocess): "
                               f"fetched={bool(src)} compiles={ok}")
            with open(_rr.LEDGER, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(row) + "\n")
        except Exception:
            pass
        if ok:
            curriculum.append({"skill": s.get("skill"), "repo": repo,
                               "file": path_part,
                               "imports": s.get("imports", []),
                               "lines": s.get("lines", 0)})
        n += 1
        with open(STORE + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"skills": lib}, f, indent=1)
        os.replace(STORE + ".tmp", STORE)
    with open(CURR, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "verified_count": len(curriculum), "items": curriculum}, f, indent=1)
    print(f"[upgrader] {n} candidates examined -> {len(curriculum)} verified executable "
          f"-> Config/curriculum.json (the automatic curriculum, W1)")
    return curriculum


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 10)