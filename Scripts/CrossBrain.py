"""CROSSBRAIN: the hybrid consensus organ (the whole-roster's models in
ONE decision): the task-class routes (the editable map) + the cross-model
parallel votes (the 120b + the 2 qwens simultaneously - the DIVERSITY
ensemble, stronger than the same-model K-votes per the canon's ensemble
class) + the dissent = the 120b's arbiter-round. $0.00 always."""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
ROUTES = os.path.join(ROOT, "Config", "hybrid_routes.json")

ROUTES_DEFAULT = {
    "judge": ("groq", "local-coder", "local-fast"),
    "draft": ("local-coder", "local-fast"),
    "translate": ("groq", "local-coder"),
    "vote": ("groq", "local-coder", "local-fast"),
    "copy": ("groq", "local-coder"),
}


def routes():
    try:
        return json.load(open(ROUTES, encoding="utf-8-sig"))
    except Exception:
        return ROUTES_DEFAULT


def ask(prompt, task_class="judge", max_tokens=400, resp_json=False):
    """The class-routed chat: the route-map's order = the hybrid's decision.
    The chat-class = the GROQ-LOCKED (the founder's directive): 3 tries on
    the first lane before the floor serves (the honest 429-handling)."""
    r = list(routes().get(task_class) or ROUTES_DEFAULT["judge"])
    import CloudBrain as CB
    tries_first = 3 if task_class == "chat" else 1
    out = None
    for attempt in range(tries_first):
        out = CB.chat(prompt, max_tokens=max_tokens,
                      purpose=f"the crossbrain {task_class}",
                      models=tuple(r), resp_json=resp_json)
        if out:
            if attempt:
                print(f"[crossbrain] the chat-lane's {r[0]} served on "
                      f"try {attempt + 1} (the rate-lane's patience)")
            return out
        print(f"[crossbrain] {task_class}: the lead-lane {r[0]} skipped "
              f"(try {attempt + 1}) - the retry/honest-fallback follows")
    return out


def cross_consensus(ask_text, k=None, expects=None):
    """THE INNOVATION: one vote PER LANE (the different models), parallel;
    the unanimous/majority = the verdict; the tie = the 120b's arbiter
    round (a second, deeper ask). The receipt = every lane's vote."""
    lanes = routes().get("vote") or ROUTES_DEFAULT["vote"]
    if k:
        lanes = lanes[:k]
    import CloudBrain as CB
    votes = []

    def _vote(lane):
        t0 = time.time()
        r = CB.chat(ask_text, max_tokens=200, purpose=f"the cross-vote {lane}",
                    models=(lane,))
        return {"lane": lane, "vote": (r or "")[:120],
                "s": round(time.time() - t0, 2)}

    with ThreadPoolExecutor(max_workers=len(lanes)) as ex:
        votes = list(ex.map(_vote, lanes))
    vals = [v["vote"] for v in votes if v["vote"].strip()]
    uniq = {}
    for v in vals:
        uniq[v] = uniq.get(v, 0) + 1
    if not vals:
        return {"verdict": "NO-VOTES (honest)", "votes": votes}
    if len(uniq) == 1:
        return {"verdict": "UNANIMOUS", "winner": vals[0], "votes": votes}
    top = max(uniq.items(), key=lambda kv: kv[1])
    if top[1] > len(vals) / 2:
        return {"verdict": "MAJORITY", "winner": top[0], "votes": votes}
    # the tie: the arbiter round (the deep-judge lane only)
    arb = CB.chat('Two different model-lanes disagree on this vote. '
                  "Break the tie with the correct answer ONLY (same JSON "
                  "shape):\n" + ask_text, max_tokens=300,
                  purpose="the crossbrain arbiter", models=("groq",))
    return {"verdict": "TIE->ARBITER", "arbiter": (arb or "")[:120],
            "votes": votes}


def selftest():
    out = {}
    # (1) the route-resolution (pure)
    out["routes"] = routes().get("judge", ROUTES_DEFAULT["judge"])
    # (2) the LIVE cross-consensus: the 3 lanes vote the same deterministic
    # ask in ONE parallel wave - the hybrid's real shape
    cc = cross_consensus('Reply ONLY the JSON {"ok": 1}.')
    out["consensus"] = {"verdict": cc["verdict"],
                        "lanes": [v["lane"] for v in cc["votes"]],
                        "times": [v["s"] for v in cc["votes"]]}
    ok = cc["verdict"] in ("UNANIMOUS", "MAJORITY") and len(
        out["consensus"]["lanes"]) >= 2
    with open(os.path.join(ROOT, "Config", "crossbrain_receipt.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "verdict": "PASS" if ok else "CHECK", **out,
                   "cost": "$0.00"}, f, ensure_ascii=False, indent=1)
    print(f"[crossbrain] PASS={ok} | consensus {cc['verdict']} | "
          f"lanes {out['consensus']['lanes']} | times "
          f"{out['consensus']['times']}")


if __name__ == "__main__":
    selftest()