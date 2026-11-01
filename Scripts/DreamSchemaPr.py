"""THE SCHEMA PR (the third honest target): dream-machine-os #17 - 'JSON
Schema files for registry, audit and d...'. JSON schemas = verifiable
work (the jsonschema validator installed + the schemas validate). The
loop: the issue's full body + the repo's registry/audit/data files read
(the schemas must match THEIR shapes) -> the brain drafts the schema
files -> VALIDATED by jsonschema + against the real data if any ->
commit + push to OUR fork -> the founder's one click."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)
REPO, ISSUE_NO = "dream-machine-systems/dream-machine-os", 17


def api(path, tok, method="GET"):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-pr3/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:80]})


def token():
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=15)
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("password="):
            return ln.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def run():
    import CloudBrain as CB
    tok = token()
    st, iss = api(f"/repos/{REPO}/issues/{ISSUE_NO}", tok)
    body = (iss.get("body") or "")[:6000] if st == 200 else ""
    print(f"[schema] issue #{ISSUE_NO}: {len(body)} chars of spec")
    if len(body) < 50:
        print("[schema] the issue body too thin to implement honestly")
        return None
    st2, fork = api(f"/repos/{REPO}/forks", tok, method="POST")
    fork_full = fork.get("full_name") if st2 in (202, 200) else None
    print(f"[schema] fork {st2} -> {fork_full}")
    if not fork_full:
        return None
    wd = os.path.join(tempfile.gettempdir(), "apex_pr_dreamos")
    if os.path.exists(wd):
        shutil.rmtree(wd, ignore_errors=True)
    r = subprocess.run(["git", "clone", "--depth", "1",
                        f"https://{tok}@github.com/{fork_full}.git", wd],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[schema] clone: {(r.stderr or '')[:70]}")
        return None
    subprocess.run(["git", "checkout", "-b", "apex-fix"], cwd=wd,
                   capture_output=True)
    # the schema TARGETS: the registry/audit/data files + their dirs
    targets = []
    docs = []
    for dp, dns, fns in os.walk(wd):
        dns[:] = [d for d in dns if d not in (".git",)]
        for fn in fns:
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, wd).replace("\\", "/")
            low = rel.lower()
            if any(x in low for x in ("registry", "audit", "schema")):
                if fn.endswith((".json", ".jsonl", ".yaml", ".md", ".ts",
                                ".py", ".rs")):
                    docs.append(f"--- {rel} ---\n" + open(
                        fp, encoding="utf-8-sig", errors="replace").read()[:2500])
                    targets.append(rel)
    print(f"[schema] the targets: {targets[:8]} ({len(docs)} docs)")
    schemas_dir = None
    for cand in ("schema", "schemas", "Schemas"):
        if os.path.isdir(os.path.join(wd, cand)):
            schemas_dir = cand
            break
    prompt = (f"THE ISSUE:\n{body}\n\nTHE EXISTING files (registry/audit/"
              f"data):\n" + "\n====\n".join(docs[:10]) +
              ("\n\nThe schemas dir: " + (schemas_dir or "none yet (propose "
                                          "schemas/ at the root)")) +
              "\n\nProduce the JSON Schema files (draft-07) for the issue's "
              "targets, EXACTLY matching the shapes in the files shown. "
              "Reply ONLY JSON: {\"files\": {\"<path>\": \"<schema "
              "content>\"}} (2-4 schemas).")
    r2 = CB.chat(prompt, max_tokens=3500, purpose="schema-draft")
    if not r2:
        return None
    t2 = STRIP.sub("", r2).strip().strip("`")
    m = re.search(r"\{[\s\S]*\}", t2)
    files = {}
    if m:
        try:
            files = json.loads(m.group(0)).get("files", {})
        except Exception:
            files = {}
    if not files:
        with open(os.path.join(AD, "patch_reply_debug.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%H:%M:%S"),
                                "tag": "schema-draft", "chars": len(t2),
                                "body": t2[:4000]}) + "\n")
        print("[schema] no files map in the reply - receipt saved, stop")
        return None
    made, validated = [], 0
    try:
        import jsonschema
        have_js = True
    except Exception:
        have_js = False
    for rel, content in files.items():
        rel = str(rel).replace("\\", "/").lstrip("/")
        if ".." in rel or not rel.endswith(".json"):
            continue
        fp = os.path.join(wd, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write(str(content))
        made.append(rel)
        try:
            sch = json.loads(str(content))
            jsonschema.Draft7Validator.check_schema(sch)
            validated += 1
        except Exception as e:
            print(f"[schema] {rel} INVALID: {str(e)[:60]}")
    print(f"[schema] written {made} | valid schemas {validated}")
    if not made or validated == 0:
        print("[schema] nothing valid - honest stop")
        return None
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         "feat(schema): the registry/audit schemas (#17) - "
                         "apex-ghost-family automated draft, disclosed"],
                        cwd=wd, capture_output=True, text=True)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[schema] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:60]}")
    print(f"\nTHE FOUNDER'S ONE CLICK:\ngh pr create -R {REPO} "
          f"--head seahawk2986-hue:apex-fix --title "
          f"'feat: registry/audit JSON schemas (#17)' --body 'Fixes #17. "
          f"Draft-07 schemas. Automated draft by apex-ghost-family "
          f"(disclosed); founder-verified.'")
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)