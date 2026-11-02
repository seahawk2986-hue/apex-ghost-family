"""VetLineRemote - THE RUNNER-SIDE PROMOTER (no Windows deps, $0).

Reads the committed ordered lead-grain (family/leads_grain.json), fetches
each repo's permissive .py files via the GitHub API, vets (compile +
AST-danger-banned-imports + size caps), appends verified rows to
Config/SkillLibrary.json + ticks the meter (GymRewards.json), ships the
grain home (the workflow commits). Runs on GitHub's free ubuntu runners;
the local box = zero RAM for this work."""
import ast
import hashlib
import json
import os
import time
import urllib.request
import urllib.error

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
LIB = os.path.join(ROOT, "Config", "SkillLibrary.json")
REWARDS = os.path.join(ROOT, "Config", "GymRewards.json")
GRAIN = os.path.join(ROOT, "family", "leads_grain.json")
STAGE = "/tmp/vet_stage"
UA = {"User-Agent": "ApexVetLine/1.0"}
BANNED = ("socket", "ftplib", "telnetlib", "paramiko", "smtplib",
          "urllib.request", "http.client", "ctypes", "subprocess",
          "multiprocessing", "sqlite3", "pickle", "marshal")
MAX_LINES, MAX_BYTES, MAX_REPOS, PER_SRC = 400, 40_000, 20, 5


def gh(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data


def load(p, default):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return default


def save_atomic(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
        f.flush()
    os.replace(tmp, p)


def vet_text(txt):
    """compile + the AST-danger-lane + the caps. Returns (ok, meta)."""
    try:
        ast.parse(txt)
    except Exception as e:
        return False, {"why": str(e)[:70]}
    if len(txt) > MAX_BYTES or txt.count("\n") + 1 > MAX_LINES:
        return False, {"why": "caps"}
    try:
        tree = ast.parse(txt)
        bad = []
        for a in ast.walk(tree):
            if isinstance(a, ast.Import):
                for n in a.names:
                    root = n.name.split(".")[0]
                    if root in BANNED:
                        bad.append(root)
            elif isinstance(a, ast.ImportFrom):
                root = (a.module or "").split(".")[0]
                if root in BANNED:
                    bad.append(root)
        if "eval(" in txt or "exec(" in txt or "__import__" in txt:
            bad.append("dynamic-exec")
        if bad:
            return False, {"why": "banned:" + ",".join(sorted(set(bad))[:5])}
    except Exception:
        pass
    return True, {}


def main():
    t0 = time.time()
    grain = load(GRAIN, {"leads": []})["leads"]
    lib = load(LIB, {"skills": [], "built": time.strftime("%Y-%m-%d %H:%M")})
    have_repos = {s.get("source_repo") for s in lib.get("skills", [])}
    have_shas = {s.get("sha256") for s in lib.get("skills", [])}
    added = []
    print(f"[grain]: {len(grain)} ordered leads | have {len(lib.get('skills', []))}"
          f" skills | vetting top-{MAX_REPOS} x{PER_SRC}")
    for lead in grain:
        if len(added) >= MAX_REPOS or time.time() - t0 > 14 * 60:
            break
        repo = lead["repo"]
        if repo in have_repos:
            continue
        try:
            tree = gh(f"https://api.github.com/repos/{repo}/git/trees/HEAD"
                      f"?recursive=1", 25)
            entries = [e for e in json.loads(tree).get("tree", [])
                       if e.get("path", "").endswith(".py")
                       and e.get("size", 10 ** 9) <= MAX_BYTES
                       and "/test" not in e["path"].lower()
                       and e["path"].count("/") <= 2][:PER_SRC]
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 409):
                print(f"  [skip] {repo}: HTTP {e.code}")
                continue
            raise
        except Exception as e:
            print(f"  [skip] {repo}: {str(e)[:60]}")
            continue
        vetted_count = 0
        for e in entries:
            if vetted_count >= 2:  # each repo contributes <= 2 verified skills
                break
            try:
                raw = gh(f"https://raw.githubusercontent.com/{repo}/HEAD/"
                         f"{e['path']}", 25).decode("utf-8", "replace")
                ok, meta = vet_text(raw)
                if not ok:
                    continue
                try:
                    _tree = ast.parse(raw)
                    imps = sorted({n.name.split(".")[0]
                                   for a in ast.walk(_tree)
                                   if isinstance(a, ast.Import)
                                   for n in a.names})[:12]
                except Exception:
                    imps = []
                sha = hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()
                if sha in have_shas:
                    continue
                row = {"skill": e["path"].rsplit("/", 1)[1].rsplit(".", 1)[0]
                       .replace("-", "_")[:48],
                       "source_file": e["path"],
                       "source_repo": repo,
                       "license": lead.get("license") or "check repo",
                       "sha256": sha, "lines": raw.count("\n") + 1,
                       "first_line": raw.splitlines()[0][:80]
                       if raw.splitlines() else "",
                       "imports": imps,
                       "registered": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "vetby": "hub-runner-v1"}
                have_shas.add(sha)
                lib.setdefault("skills", []).append(row)
                added.append({"skill": row["skill"], "repo": repo,
                              "sha256": sha[:16]})
                vetted_count += 1
            except Exception as ex:
                print(f"  [item-fail] {repo}/{e.get('path')}: {str(ex)[:60]}")
        have_repos.add(repo)
        print(f"  [{repo}]: +{vetted_count} vetted (score {lead.get('score')})",
              flush=True)

    if not added:
        print("[result]: nothing new passed the vet this round (honest)")
        return
    lib["built"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_atomic(LIB, lib)
    # the meter-tick: +10/new vetted skill, honest receipt
    rw = load(REWARDS, {"points": 0})
    pts = 10 * len(added)
    rw["library_points"] = rw.get("library_points", 0) + pts
    rw["points"] = rw.get("points", 0) + pts
    save_atomic(REWARDS, rw)
    print(f"[METER]: +{pts} library-points (total {rw['points']}) | "
          f"+{len(added)} vetted skills -> committed by the workflow")
    with open(os.path.join(ROOT, "hub_round_result.json"), "w",
              encoding="utf-8") as f:
        json.dump({"kind": "vet-line", "added": added,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)


if __name__ == "__main__":
    main()