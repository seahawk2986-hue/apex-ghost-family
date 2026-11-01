"""PATCH LOOP v3 (the honest lessons applied): the blind-select fixed.
 - THE LANGUAGES DETECTED first (the tree's extension census - the locator
   was .py/.js-blind on a non-python repo);
 - THE SHORTLIST: the issue's terms ranked across the REAL source files
   (term-hits per file, top-10) + the content SNIPPETS for the top-5 land
   IN the select prompt - the brain chooses with evidence;
 - the DRAFT then works on 3 chosen CODE files; 1 apply-retry; <= 4 calls.
The drain gate holds the whole loop (each call ledgered, the cap enforced)."""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
STATE = os.path.join(AD, "pr_pipeline_state.json")
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)


def run():
    import CloudBrain as CB
    import PatchStep as PS
    state = json.load(open(STATE, encoding="utf-8-sig"))
    repo, wd = state["repo"], state["workspace"]
    if not os.path.isdir(wd):
        print("[v3] the workspace is gone - rerun PrPipeline.py")
        return None
    tok = PS.token()
    st, issues = PS.api(f"/repos/{repo}/issues?state=open&per_page=30", tok)
    body, issue_no = "", None
    for it in (issues if st == 200 else []):
        if "muse" in ((it.get("title", "") + (it.get("body") or "")).lower()):
            issue_no, body = it.get("number"), (it.get("body") or "")[:4000]
            break
    if not issue_no:
        print("[v3] the issue not found - honest stop")
        return None
    tree = [x for x in subprocess.run(["git", "ls-files"], cwd=wd,
                                      capture_output=True, text=True,
                                      timeout=60).stdout.splitlines() if x]
    langs = Counter(os.path.splitext(x)[1].lower() for x in tree)
    src_exts = [e for e, n in langs.most_common(5)
                if e in (".go", ".rs", ".py", ".js", ".ts", ".c", ".cpp",
                         ".sh", ".mjs", ".lua")]
    exts_use = src_exts or [e for e, _ in langs.most_common(3)]
    print(f"[v3] languages: {dict(langs.most_common(6))} -> using {exts_use}")
    terms = list(dict.fromkeys(
        w for w in re.split(r"\W+", (state.get("issue", "") + " muse hook")
                            .lower()) if len(w) > 3))[:10]
    ranked = []
    for x in tree:
        if os.path.splitext(x)[1].lower() not in exts_use:
            continue
        try:
            t = open(os.path.join(wd, x), encoding="utf-8-sig",
                     errors="replace").read().lower()
        except Exception:
            continue
        n = sum(1 for tm in terms if tm in t)
        if n:
            ranked.append((x, n))
    ranked.sort(key=lambda kv: -kv[1])
    short = [x for x, _ in ranked[:10]]
    print(f"[v3] the term-ranked shortlist: {short}")
    if not short:
        print("[v3] no term hits in source files - honest stop")
        return None
    snippets = []
    for rel in short[:5]:
        t = open(os.path.join(wd, rel), encoding="utf-8-sig",
                 errors="replace").read()
        low = t.lower()
        where = 0
        for tm in terms:
            ix = low.find(tm)
            if ix >= 0:
                where = ix
                break
        snippet = t[max(0, where - 200): where + 1400]
        snippets.append(f"--- {rel} (context) ---\n{snippet}")
    sel = CB.chat(
        f"ISSUE #{issue_no}:\n{body[:1500]}\n\nSNIPPETS:\n" +
        "\n".join(snippets) +
        '\n\nReply ONLY JSON: {"read": ["<up to 3 file paths, full>", '
        '"..."], "change_plan": "<=250 chars"}', max_tokens=350,
        purpose="v3-select")
    if not sel:
        return None
    m = re.search(r"\{.*\}", STRIP.sub("", sel), re.S)
    files, cplan = [], ""
    if m:
        try:
            j = json.loads(m.group(0))
            files, cplan = j.get("files", [])[:3], j.get("change_plan", "")
        except Exception:
            pass
    if not files:
        files = short[:3]
    print(f"[v3] the read set: {files} | plan: {cplan[:140]}")
    texts = []
    for rel in files:
        try:
            texts.append(f"{rel}:\n" + open(os.path.join(wd, rel),
                                            encoding="utf-8-sig",
                                            errors="replace").read()[:7000])
        except Exception:
            pass
    diff = CB.chat(f"ISSUE #{issue_no}:\n{body[:1500]}\nPLAN: {cplan}\n\n" +
                   "\n====\n".join(texts) +
                   "\n\nWrite the change as a UNIFIED DIFF (git apply "
                   "format, a/ b/ paths). Reply ONLY one ```diff block.",
                   max_tokens=2500, purpose="v3-draft")
    if not diff:
        return None
    diff = STRIP.sub("", diff).strip()
    if "```diff" in diff:
        diff = diff[diff.index("```diff") + 7: diff.rindex("```")]
    for attempt in (1, 2):
        pd = os.path.join(wd, "apex.patch")
        open(pd, "w", encoding="utf-8").write(diff)
        r = subprocess.run(["git", "apply", "--check", pd], cwd=wd,
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            break
        print(f"[v3] apply-check failed ({attempt}): {(r.stderr or '')[:90]}")
        if attempt == 2:
            print("[v3] honest stop - the diff never applied; the LOCATED "
                  "evidence + the plan are in patch_state for the founder")
            with open(os.path.join(AD, "patch_state.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                           "issue": issue_no, "applied": False,
                           "plan": cplan, "files": files,
                           "shortlist": short}, f, indent=1)
            return None
        fix = CB.chat("The diff failed to apply: " + (r.stderr or "")[:400] +
                      "\n\nThe diff:\n" + diff[:3500] +
                      "\nReply ONLY the corrected ```diff block.",
                      max_tokens=2500, purpose="v3-fix")
        if not fix:
            return None
        fix = STRIP.sub("", fix).strip()
        if "```diff" in fix:
            diff = fix[fix.index("```diff") + 7: fix.rindex("```")]
    subprocess.run(["git", "apply", pd], cwd=wd, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         f"fix: hook muse (issue #{issue_no}) - "
                         f"apex-ghost-family automated draft, disclosed"],
                        cwd=wd, capture_output=True, text=True, timeout=60)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[v3] commit rc={cm.returncode} | push rc={ph.returncode} "
          f"{(ph.stderr or '')[:80]}")
    print(f"\n[v3] THE FOUNDER'S ONE CLICK:\ngh pr create -R {repo} "
          f"--head seahawk2986-hue:apex-fix --title 'fix: hook muse "
          f"(#{issue_no})' --body 'Fixes #{issue_no}. Automated draft by "
          f"apex-ghost-family (disclosed); founder-verified.'")
    with open(os.path.join(AD, "patch_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "issue": issue_no, "applied": True, "pushed":
                   ph.returncode == 0, "plan": cplan, "files": files}, f,
                  indent=1)
    return cm.returncode == 0 and ph.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)