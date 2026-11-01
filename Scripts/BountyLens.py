"""THE BOUNTY LENS - the income upgrade: the discovery flips from 'any
gfi' to the $-LABELED issues ONLY (the marketplaces' real money labels:
algora's emoji-rates, the bounty/$ labels, the money-amounts in the
labels). GitHub's search: label:"💰 bounty" / the $ regex on the labels.
Every hit: the claim-audit + the EV (the label's parsed $ amount / the
complexity's estimate) -> the EARN QUEUE (the honest targets = the
real-funded jobs). Reads NOTHING paid; free APIs only."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(AD, "earn_queue.json")
DOLLAR = re.compile(r"\$\s?([1-9]\d{1,5})")


def token():
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=15)
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("password="):
            return ln.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def api(path, tok):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-bounty-lens/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:60]})


def run():
    tok = token()
    hits = []
    # the $-labeled issues (the REAL money labels across the ecosystem)
    queries = [
        'label:"💰 bounty" type:issue state:open sort:created-desc',
        'label:"algora" type:issue state:open sort:created-desc',
        'label:"💰 reward" type:issue state:open',
    ]
    for q in queries:
        st, d = api("/search/issues?q=" + urllib.parse.quote(q) +
                    "&per_page=25", tok)
        for it in (d.get("items") or []):
            labels = [l.get("name", "") for l in it.get("labels", [])]
            money = 0.0
            for l0 in labels:
                m = DOLLAR.search(l0)
                if m:
                    money = max(money, float(m.group(1)))
            if not money:
                m2 = DOLLAR.search(it.get("title", "") + " "
                                   + (it.get("body") or "")[:300])
                money = float(m2.group(1)) if m2 else 0.0
            if money >= 25:
                hits.append({"repo": it.get("repository_url", "")
                             .rsplit("/", 2)[-2:] and
                             "/".join(it.get("repository_url", "")
                                      .rsplit("/", 2)[-2:]),
                             "issue": it.get("number"),
                             "labels": labels[:5], "bounty_usd": money,
                             "state": it.get("state"),
                             "lang_guess": (it.get("repository_url", "")
                                            .rsplit("/", 1)[-1])})
            if len(hits) >= 40:
                break
        time.sleep(1)
    # the claim-check on each (the etiquette stays)
    import ClaimCheck as CC
    import PatchStep as PS
    queue = []
    for h0 in hits[:15]:
        if not h0["repo"]:
            continue
        linked, claim_c, assigned = CC.check_issue(PS.api, h0["repo"],
                                                   h0["issue"], tok)
        if linked + claim_c + assigned:
            continue                      # claimed -> never collided
        queue.append(h0)
    queue.sort(key=lambda x: -x["bounty_usd"])
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "found_labeled": len(hits),
           "unclaimed_queue": queue,
           "total_bounty_pool_usd": sum(q0["bounty_usd"] for q0 in queue),
           "law": "the queue = REAL posted bounties, claim-audited; "
                  "the machine works them via the claim-audited pipeline; "
                  "the payout = the platform's escrow (the founder's "
                  "identity links the payment)"}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    print(f"[bounty-lens] found {len(hits)} $-labeled issues, "
          f"unclaimed {len(queue)} | the pool: "
          f"${doc['total_bounty_pool_usd']:.0f}")
    for q0 in queue[:6]:
        print(f"   ${q0['bounty_usd']:6.0f} | {q0['repo']} "
              f"#{q0['issue']} | {q0['labels']}")
    return doc


if __name__ == "__main__":
    run()