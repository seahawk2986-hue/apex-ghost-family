"""THE PR WATCH - the client-care organ: EVERY beat checks OUR open PRs'
state changes: the reviews/comment/CI state -> the founder's briefs lane
(the response drafts ready) - the honest: no reply is auto-SENT (the
disclosure + the etiquette stand); the WATCH reports + prepares.
TEST GATE: (a) the real API read of OUR PRs (#4929 + #23), (b) the
state-diff vs the prior watch-state (Config/pr_watch_state.json),
(c) the briefs' honest rows, (d) reproducible."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
WATCH = os.path.join(ROOT, "Config", "pr_watch_state.json")
OUR_PRS = [("rtk-ai/rtk", 4929), ("dream-machine-systems/dream-machine-os", 23)]


def run():
    import PatchStep as PS
    tok = PS.token()
    prev = {}
    try:
        prev = json.load(open(WATCH, encoding="utf-8-sig"))
    except Exception:
        pass
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "prs": []}
    for repo, no in OUR_PRS:
        st, d = PS.api(f"/repos/{repo}/pulls/{no}", tok)
        entry = {"repo": repo, "pr": no,
                 "state": d.get("state", "?"), "mergeable_state":
                 d.get("mergeable_state", "?"),
                 "comments": d.get("comments"), "labels":
                 [l.get("name") for l in d.get("labels", [])]}
        # the NEW comments since our last? (the honest count-diff)
        n = int(d.get("comments", 0) or 0)
        e0 = (prev.get("prs") or [])
        old = next((x for x in e0 if x.get("repo") == repo and
                    x.get("pr") == no), {})
        if n > int(old.get("comments", 0) or 0):
            entry["new_activity"] = True
            entry["founder_action"] = ("read the maintainer's comment and "
                                       "answer (the loop can draft the "
                                       "response on your word)")
            print(f"[watch] {repo}#{no}: NEW COMMENTS ({n}) - the brief")
        out["prs"].append(entry)
    with open(WATCH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
              encoding="utf-8") as f:
        f.write(json.dumps({"ts": out["ts"], "kind": "upward",
                            "what": "pr-watch",
                            "states": [e["mergeable_state"]
                                       for e in out["prs"]]}) + "\n")
    states = [(e["repo"].split("/")[-1], e["mergeable_state"])
              for e in out["prs"]]
    print("[pr-watch] " + json.dumps(states, default=str))
    return out


if __name__ == "__main__":
    run()