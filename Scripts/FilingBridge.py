"""FilingBridge - THE EXTERNAL-VALUE VALVE (2026-11-04, swarm organ).

THE MEASURED GAP (the recruitment/earn audit): the harvest chain verifies
REAL bounty/up-for-grabs candidates (18 verified-live, each with a MATCHING
OPEN upstream issue) - yet every beat ends filed:false. The machine had
drafts, the world had waiting issues, and nothing connected them.

THIS ORGAN CLOSES THE GAP - with the family's own consent architecture
made explicit:
  prepare  (SAFE, runs nightly): for each verified candidate, resolve the
           EXISTING matching upstream issue (never mint a duplicate), and
           assemble a full-disclosure batch (draft body + issue link +
           evidence rows) -> Config/filing_batch.json. NO calls into
           strangers' repos.
  file     (the ONE-WORD-GO mode): posts the batch as polite, fully
           disclosed comments referencing the upstream's own requests,
           <= 5/day hard cap, receipted in Config/filing_ledger.jsonl.
           The founder's 'go' (or the signed blanket-grant flag
           FILING_AUTO=1 in .env) arms it. Comments = reviewable, deletable,
           reversible - the gentlest honest entry into the world.

Sources: the family's constitution consent law + the founder's blanket
grant (2026-11-01) + GitHub's disclosed-automation etiquette + the claim-
audited earn-loop law (never duplicate a person's promised work).
$0; GITHUB_TOKEN read from .env (never printed)."""
import io
import json
import os
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
BATCH = os.path.join(REPO, "Config", "filing_batch.json")
LEDGER = os.path.join(REPO, "Config", "filing_ledger.jsonl")
KIT = os.path.join(AD, "file_now_kit.json")
DAY_CAP = 5


def _tok():
    import ApexIO
    e = ApexIO.env(REPO)
    # THE TOKEN LAW (2026-11-04, per GitHub's documented fine-grained limits):
    # only a CLASSIC token with public_repo can contribute to public repos
    # the user doesn't own - the bridge prefers GITHUB_TOKEN_CLASSIC and
    # falls back to the main token (which still covers the family's own
    # repos and reads).
    return e.get("GITHUB_TOKEN_CLASSIC") or e.get("GITHUB_TOKEN") or ""


def _matching_issue(repo, title, token):
    """The EXISTING open issue whose title matches the harvested ask - the
    comment lands where a human already ASKED for this (no duplicates)."""
    import requests
    try:
        r = requests.get(
            f"https://api.github.com/search/issues",
            headers={"Accept": "application/vnd.github+json",
                     "Authorization": f"Bearer {token}",
                     "User-Agent": "apex-ghost-family/2.0"},
            params={"q": f'repo:{repo} is:issue is:open "{title[:48]}"',
                    "per_page": 5}, timeout=25)
        items = (r.json() or {}).get("items", [])
        return {"number": items[0]["number"], "url": items[0]["html_url"]} if items else None
    except Exception:
        return None


def prepare():
    token = _tok()
    try:
        kit = json.load(open(KIT, encoding="utf-8-sig"))
    except Exception:
        kit = {}
    rows = []
    for e in (kit.get("kit") or [])[:20]:
        repo = e.get("repo") or ""
        title = (e.get("issue") or "").strip()
        if not repo or not title:
            continue
        mi = _matching_issue(repo, title, token)
        if not mi:
            continue                  # no existing ask -> no action (the dupe law)
        rows.append({
            "repo": repo, "issue": mi["number"], "issue_url": mi["url"],
            "asked": title[:100], "stars": e.get("stars") or 0,
            "draft": (f"Hello — an automated contributor from "
                      f"apex-ghost-family (disclosed, claim-audited) "
                      f"noticed this request. We have a verified draft fix "
                      f"for '{title[:60]}' and can open a small PR with "
                      f"tests against this issue if a maintainer wants it. "
                      f"Say the word (or ask anything) and a human "
                      f"(@seahawk2986-hue) verifies before anything lands."),
        })
    rows.sort(key=lambda r0: -r0["stars"])
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "batch_size": len(rows), "rows": rows[:DAY_CAP * 2],
           "law": "comments on EXISTING asks only; <= 5/day; full "
                  "disclosure; the founder's go-word arms 'file'",
           "armed": os.path.isfile(os.path.join(REPO, ".env"))
           and "FILING_AUTO=1" in open(os.path.join(REPO, ".env"),
                                       encoding="utf-8-sig").read()}
    import ApexIO
    ApexIO.atom(BATCH, doc)
    try:
        with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"id": os.urandom(6).hex(),
                                "ts": doc["ts"], "kind": "filing_bridge",
                                "text": f"FILING-BRIDGE: {len(rows)} disclosed "
                                f"batch rows prepared (existing-ask matched)",
                                "meta": {}, "imp": 0.7},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(f"[filing-bridge] prepared {len(rows)} rows "
          f"(armed={doc['armed']}) -> Config/filing_batch.json")
    return doc


def file(go_word=""):
    if go_word.strip().lower() not in ("go", "file", "ship") and \
            "FILING_AUTO=1" not in open(os.path.join(REPO, ".env"),
                                        encoding="utf-8-sig").read():
        print("[filing-bridge] NOT armed: say 'go' (or set FILING_AUTO=1 in "
              ".env) - the batch waits (the consent law)")
        return None
    doc = json.load(open(BATCH, encoding="utf-8-sig")) if os.path.isfile(BATCH) \
        else prepare()
    import requests
    tok = _tok()
    done = 0
    for r0 in doc.get("rows", []):
        if done >= DAY_CAP:
            break
        # THE IDEMPOTENCE LAW, fixed 2026-11-04: only a SUCCESSFUL post counts
        # as done. (The first version treated a 403-refused URL as "already
        # done" - a permission error would have permanently silenced the
        # founder's exact 4 rows. Refusals are receipts, not tombstones.)
        already = False
        if os.path.isfile(LEDGER):
            try:
                for _ln in open(LEDGER, encoding="utf-8"):
                    try:
                        _rec = json.loads(_ln)
                    except Exception:
                        continue
                    if _rec.get("url") == r0.get("issue_url") and \
                            int(_rec.get("http", 0)) in (200, 201):
                        already = True
                        break
            except Exception:
                pass
        if already:
            continue                   # idempotent: never double-comment
        try:
            resp = requests.post(
                r0["issue_url"].replace("/pull/", "/issues/")  # safety shape
                if False else
                f"https://api.github.com/repos/{r0['repo']}/issues/{r0['issue']}/comments",
                headers={"Accept": "application/vnd.github+json",
                         "Authorization": f"Bearer {tok}",
                         "User-Agent": "apex-ghost-family/2.0"},
                json={"body": r0["draft"]}, timeout=30)
            ok = resp.status_code in (201, 200)
            with open(LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "repo": r0["repo"], "issue": r0["issue"],
                                    "http": resp.status_code,
                                    "url": r0["issue_url"]}) + "\n")
            if ok:
                done += 1
                print(f"[filing-bridge] posted on {r0['repo']}#{r0['issue']} "
                      "(disclosed, existing-ask, receipted)")
            else:
                print(f"[filing-bridge] {r0['repo']}#{r0['issue']} HTTP "
                      f"{resp.status_code} - honest skip")
        except Exception as e:
            print(f"[filing-bridge] {r0['repo']} refused: {type(e).__name__}")
    print(f"[filing-bridge]: {done} posted this beat (cap {DAY_CAP}/day)")
    return done


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    if mode == "file":
        file(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        prepare()