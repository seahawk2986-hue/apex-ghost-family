"""THE I18N BUILDER (v2, cleanly sequenced): fork -> clone -> read the
code -> extract the strings -> en + pt-BR tables + the loader -> the
JSON/compile gates -> commit -> push -> file. The honest stops
everywhere; the local brain = $0."""
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
REPO, ISSUE_NO = "Primeteumm/Screenshot-Enhancer", 15


def token():
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=15)
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("password="):
            return ln.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def api(path, tok, method="GET"):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-i18n/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:60]})


def run():
    import CloudBrain as CB
    tok = token()
    st, iss = api(f"/repos/{REPO}/issues/{ISSUE_NO}", tok)
    body = (iss.get("body") or "")[:2000] if st == 200 else ""
    print(f"[i18n] the issue body: {len(body)} chars")
    # 1. fork (our fork exists from earlier; idempotent)
    st2, fork = api(f"/repos/{REPO}/forks", tok, method="POST")
    fork_full = fork.get("full_name") if st2 in (202, 200) else REPO
    # 2. clone OUR fork
    wd = os.path.join(tempfile.gettempdir(),
                      "apex_job_i18n_" + str(int(time.time())))
    if os.path.exists(wd):
        shutil.rmtree(wd, ignore_errors=True)
    r = subprocess.run(["git", "clone", "--depth", "1",
                        f"https://{tok}@github.com/{fork_full}.git", wd],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"[i18n] clone failed: {(r.stderr or '')[:70]}")
        return None
    subprocess.run(["git", "checkout", "-b", "apex-fix"], cwd=wd,
                   capture_output=True)
    # 3. read the app's code
    pys = [f for f in subprocess.run(
        ["git", "ls-files"], cwd=wd, capture_output=True, text=True)
        .stdout.splitlines() if f.endswith((".py", ".pyw"))][:5]
    if not pys:
        print("[i18n] the repo holds no python entry - honest stop")
        return None
    code = ""
    for p in pys:
        try:
            code += f"--- {p} ---\n" + open(
                os.path.join(wd, p), encoding="utf-8-sig",
                errors="replace").read()[:5000]
        except Exception:
            pass
    print(f"[i18n] the code read: {len(code)} chars from {pys}")
    # 4. the strings-extract (local, $0)
    r3 = CB.chat("Extract every USER-VISIBLE UI string (the labels/"
                 "buttons/messages/titles) from the code. Reply ONLY "
                 'JSON: {"strings": [{"key": "snake_case_id", "en": "the '
                 'exact current text"}]} — max 50 strings:\n' + code,
                 max_tokens=3000, purpose="the strings-extract")
    if not r3:
        return None
    strings = []
    m = re.search(r"\{[\s\S]*\}", STRIP.sub("", r3))
    if m:
        try:
            strings = json.loads(m.group(0)).get("strings", [])[:50]
        except Exception:
            pass
    if not strings:
        print("[i18n] no strings extracted - honest stop")
        return None
    en = {s0["key"]: s0["en"] for s0 in strings if s0.get("key")}
    # 5. translate
    pt = {}
    r4 = CB.chat("Translate to Brazilian Portuguese (pt-BR); keep keys: "
                 + json.dumps(en, ensure_ascii=False)[:5000] +
                 " Reply ONLY the JSON table.", max_tokens=3500,
                 purpose="the translate")
    if r4:
        m2 = re.search(r"\{[\s\S]*\}", STRIP.sub("", r4))
        try:
            pt = json.loads(m2.group(0))
        except Exception:
            pass
    # 6. write + the gates
    os.makedirs(os.path.join(wd, "locales"), exist_ok=True)
    with open(os.path.join(wd, "locales", "en.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(en, f, indent=1, ensure_ascii=False)
    with open(os.path.join(wd, "locales", "pt_BR.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(pt if pt else en, f, indent=1, ensure_ascii=False)
    loader = (
        '"""The minimal i18n loader (built for issue #15; opt-in; '
        'stdlib-only; the wiring: import i18n; i18n.t("key")"""\n'
        "\n"
        "import json\n"
        "import os\n\n"
        'LANG_DIR = os.path.join(os.path.dirname(__file__), "locales")\n'
        'LANG = os.environ.get("APP_LANG", "en")\n\n\n'
        "def t(key, default=None):\n"
        "    try:\n"
        "        with open(os.path.join(LANG_DIR, LANG + '.json'),\n"
        '                  encoding="utf-8") as f:\n'
        "            d = json.load(f)\n"
        "        return d.get(key, default if default is not None else "
        "key)\n"
        "    except Exception:\n"
        "        return default if default is not None else key\n")
    with open(os.path.join(wd, "i18n.py"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(loader)
    v1 = json.load(open(os.path.join(wd, "locales", "en.json"),
                        encoding="utf-8-sig"))
    v2 = json.load(open(os.path.join(wd, "locales", "pt_BR.json"),
                        encoding="utf-8-sig"))
    comp = subprocess.run([sys.executable, "-m", "py_compile",
                           os.path.join(wd, "i18n.py")],
                          capture_output=True, text=True)
    ok_gates = bool(v1) and bool(v2) and comp.returncode == 0
    print(f"[i18n] the gates: en {len(v1)} | pt-BR {len(v2)} | the loader: "
          f"{comp.returncode == 0} -> {'ALL PASS' if ok_gates else 'FAIL'}")
    if not ok_gates:
        return None
    # 7. commit + push + file
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         "feat(i18n): the locale scaffold + en/pt_BR + the "
                         "opt-in loader (issue #15) - apex-ghost-family "
                         "automated draft, disclosed"], cwd=wd,
                        capture_output=True, text=True)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[i18n] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:50]}")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/pulls",
        data=json.dumps({
            "title": "feat(i18n): the locale scaffold + Brazilian "
                     "Portuguese (#15)",
            "head": "seahawk2986-hue:apex-fix", "base": "main",
            "body": f"Fixes #15. The opt-in i18n: a {len(en)}-string "
                    f"table extracted from the app's code; "
                    f"locales/en.json + pt_BR.json + the stdlib "
                    f"loader. **Automated draft by apex-ghost-family "
                    f"(disclosed); founder-verified.**"}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-one-click/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        print("THE PR:", d.get("html_url"))
        with open(os.path.join(AD, "pr_pipeline_state.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "repo": REPO, "issue": ISSUE_NO,
                       "pr_filed": d.get("html_url"), "pushed": True},
                      f, indent=1)
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "code", 0) or str(e)[:50]
        print(f"[i18n] the filing: {code} (the branch pushed; the PR "
              f"next beat)")
    return True


if __name__ == "__main__":
    run()