"""THE CLAIM CHECK (the etiquette law, mechanized): the kit's candidates
scored by their issue-pages' CLAIM state:
 - the linked PRs to the SAME repo mentioning the issue ('fixes #N') =
   CLAIMED (someone's PR exists);
 - the comments carrying claim-language ('I can open a PR', 'working on
   this', 'I'll send'...) = CLAIMED (a human promised);
 - the assignment = CLAIMED.
The kit RE-RANKS: the unclaimed candidates first (the honest targets); the
claimed ones stay listed with 'skipped: claimed' (never collided).
THE FOUNDATION RULE: we do not take tasks a person has promised.
TEST GATE: (a) real API over the 18 (bounded), (b) the claim-language
detector's both classes (synthetic), (c) the kit's rerank honest,
(d) nothing auto-files."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
KIT = os.path.join(AD, "file_now_kit.json")
CLAIM_PAT = re.compile(r"(I can open|I'll (send|open|submit)|working on|"
                       r"I have (a|the) (PR|patch)|I'm on it|claimed|"
                       r"assigned to me|PR (is|coming) (up|soon))", re.I)


def check_issue(api_fn, repo, issue_no, tok):
    """One issue's claim state via the REAL tracker:
    (the linked PRs count, the claim-comments count, assigned)."""
    st1, ev = api_fn(f"/repos/{repo}/issues/{issue_no}/timeline?per_page=60",
                     tok)
    linked = 0
    for e in (ev if st1 == 200 else []):
        src_issue = ((e.get("source") or {}).get("issue") or {})
        if e.get("event") in ("cross-referenced",) and \
                src_issue.get("pull_request"):
            linked += 1
    st3, comments = api_fn(f"/repos/{repo}/issues/{issue_no}/comments"
                           "?per_page=50", tok)
    claims = sum(1 for c in (comments if st3 == 200 else [])
                 if CLAIM_PAT.search(c.get("body", "")))
    st4, issue = api_fn(f"/repos/{repo}/issues/{issue_no}", tok)
    assigned = 1 if (issue.get("assignee") if st4 == 200 else None) else 0
    # THE BODY-CLAIM (the #4917 lesson: 'I can open a PR' written in the
    # issue's OWN body is the strongest claim - the first version read
    # comments only and re-ranked a claimed issue as fair game)
    body_claim = 1 if CLAIM_PAT.search(issue.get("body", "") if st4 == 200
                                       else "") else 0
    return linked, claims + body_claim, assigned


def main():
    import PatchStep as PS
    tok = PS.token()
    kit = json.load(open(KIT, encoding="utf-8-sig"))
    out = []
    for e in kit["kit"]:
        repo = e["repo"]
        # find the issue number (the kit's issue text -> search)
        st, found = PS.api(
            f"/search/issues?q=repo:{repo}+is:issue+"
            + re.sub(r"[^a-zA-Z0-9]+", "+", e["issue"])[:60], tok)
        items = (found.get("items") or []) if st == 200 else []
        if not items:
            e["claim"] = {"state": "issue-not-found", "skipped": True}
            out.append(e)
            continue
        it = items[0]
        linked, claim_c, assigned = check_issue(PS.api, repo, it["number"], tok)
        claimed = linked + claim_c + assigned
        e["issue_no"] = it["number"]
        e["claim"] = {"linked_prs": linked, "claim_comments": claim_c,
                      "assigned": assigned,
                      "state": "CLAIMED - skipped (we never take a "
                               "person's promised work)" if claimed
                      else "UNCLAIMED - the honest target"}
        out.append(e)
        time.sleep(0.7)
    unclaimed = [e for e in out if "UNCLAIMED" in (e.get("claim") or {})
                 .get("state", "")]
    claimed = [e for e in out if e not in unclaimed]
    kit["kit"] = unclaimed + claimed       # the honest re-rank
    kit["claim_audit"] = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                          "unclaimed": len(unclaimed),
                          "claimed_skipped": len(claimed)}
    with open(KIT, "w", encoding="utf-8") as f:
        json.dump(kit, f, indent=1)
    with open(os.path.join(AD, "FILE_NOW_KIT.md"), "w",
              encoding="utf-8") as f:
        f.write("# THE FILE-NOW KIT (claim-audited, founder-gated)\n\n")
        f.write(f"UNCLAIMED targets: {len(unclaimed)} | "
                f"claimed (skipped by law): {len(claimed)}\n\n")
        for i, e in enumerate(unclaimed, 1):
            f.write(f"## {i}. {e['repo']} (stars {e['stars']})\n"
                    f"- issue #{e.get('issue_no')}: {e['issue']}\n"
                    f"- the honest work = a PR fixing it (fork+patch+"
                    f"submit; the pipeline stages it)\n\n")
        f.write("## SKIPPED (claimed by humans - never collided):\n")
        for e in claimed:
            f.write(f"- {e['repo']}: {e['claim']['state'][:60]}\n")
    print(f"[claim-check] unclaimed {len(unclaimed)} | claimed-skipped "
          f"{len(claimed)} | the kit reranked")
    return unclaimed, claimed


if __name__ == "__main__":
    u, c = main()
    for e in u[:8]:
        print(f"  TARGET (stars {e['stars']}): {e['repo']} "
              f"#{e.get('issue_no')}: {e['issue'][:50]}")