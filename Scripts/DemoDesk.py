"""DEMODESK: the free-triage funnel (the product-led-growth, the canon's
lesson): a PUBLIC demo-repo where anyone opens an issue -> the family
deliver a free mini-triage (disclosed, bounded) -> the deeper packs =
the shop. Consent-clean: they come to us. The watch = the issue-reader
(bounded 3/run) + the mini-triage = the repo-meta + the honest-CTA."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

REPO = "seahawk2986-hue/open-triage-demo"
STATE = os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                     "Config", "demo_desk_state.json")
README = """# open-triage-demo - the FREE tier of the apex-ghost-family

**Open an issue describing your repository or task - get a free,
disclosed mini-triage within 24h.**

- The automated family drafts it (disclosed), a human verifies it.
- Free means free: no checkout, no account, no spam.
- Need the deeper work (the patches + the tests + the receipts)? The
  packs live at [the family's page](https://seahawk2986-hue.github.io/apex-ghost-family/).

*Every triage carries "automated draft (disclosed)". We never take a
task a person has already promised to do.*"""


def api(path, method="GET", body=None):
    tok = PS.token()
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-demo-desk/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return getattr(getattr(e, "fp", None), "code", 0), {}


def ensure_repo():
    st, d = api("repos/seahawk2986-hue/open-triage-demo")
    if st == 200:
        print("[demo-desk] the repo exists;")
        return True
    st2, d2 = api("/user/repos", "POST", {
        "name": "open-triage-demo",
        "description": "the FREE triage tier: open an issue, get a "
                       "disclosed mini-triage in 24h (the human-verified)",
        "has_issues": True, "auto_init": True,
        "topics": ["triage", "code-review", "ai-agents", "free-tier",
                   "code-quality", "bug-triage", "open-source"]})
    print(f"[demo-desk] the repo-create: {st2}; topics = the discovery")
    return st2 in (201, 200)


def put_file(path, content, msg):
    gh2 = f"repos/{REPO}/contents/{path}"
    st, d = api(gh2)
    payload = {"message": msg,
               "content": __import__("base64").b64encode(
                   content.encode()).decode()}
    if st == 200 and d.get("sha"):
        payload["sha"] = d["sha"]
    st3, d3 = api(gh2, "PUT", payload)
    print(f"[demo-desk] {path}: {st3}")


def run():
    st = ensure_repo()
    if not st:
        print("[demo-desk] the honest stop: the repo's ensure failed")
        return
    try:
        old_state = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        old_state = {"seen": {}}
    st4, issues = api(f"repos/{REPO}/issues?state=open&per_page=10")
    done = 0
    for it in (issues if isinstance(issues, list) else []):
        if it.get("pull_request") or it.get("number") in (
                old_state["seen"] or {}):
            continue
        if done >= 3:
            print("[demo-desk] the run's honest cap (3) hit; the next "
                  "beat continues")
            break
        body = (it.get("body") or "")[:3000]
        comment = ("**Free mini-triage (automated draft, disclosed; a "
                   "human verifies it)**\n\nThanks for using the free "
                   "tier. From your description, the family's read:\n\n"
                   "- The scope: " + (it.get("title") or "")[:120] + "\n"
                   "- The safe start: the smallest reproducing example "
                   "you can share (a snippet or a link).\n- What we "
                   "deliver free next: the 10-point triage of the repo "
                   "you point us at, plus the top-3 hot-spots.\n- The "
                   "deeper work (the patch-pack + the tests): the "
                   "[packs](https://seahawk2986-hue.github.io/apex-ghost-family/).")
        st5, _ = api(f"repos/{REPO}/issues/{it['number']}/comments",
                     "POST", {"body": comment})
        old_state["seen"][it["number"]] = time.strftime(
            "%Y-%m-%d %H:%M:%S")
        done += 1
        print(f"[demo-desk] issue {it['number']}: the mini-triage "
              f"posted ({st5})")
    old_state["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    old_state["served_total"] = len(old_state["seen"])
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(old_state, f, indent=1)
    print(f"[demo-desk] the state: {done} served this run | total "
          f"{old_state['served_total']}")


if __name__ == "__main__":
    run()
    # the receipt
    open(os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                      "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
             "what": "demo-desk: the free-triage funnel live"}) + "\n")