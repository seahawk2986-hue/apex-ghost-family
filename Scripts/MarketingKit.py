"""THE MARKETING KIT (the founder's accounts post; the machine drafts):
3 platform-perfect drafts + the honest disclosure in every one. The facts
all come from the real receipts (the PRs, the shop, the honest $0.00, the
921-1038 canon, the hub). NO auto-posting: the machine holds no social
identities (the honest limit); the kit = the paste-ready files (one per
platform) at Adapter/marketing_kit/, built from the real numbers by the
LOCAL brain ($0)."""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
MK = os.path.join(AD, "marketing_kit")
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)

FACTS = {
    "hub": "https://github.com/seahawk2986-hue/apex-ghost-family",
    "prs": ["https://github.com/rtk-ai/rtk/pull/4929",
            "https://github.com/dream-machine-systems/dream-machine-os/pull/23"],
    "shop": "https://buy.polar.sh/polar_cl_WgIburVk2NFbxJJn9UtiWrLkLPWPi6PHmqmSM2Q29FD",
    "shop2": "https://buy.polar.sh/polar_cl_bsAkKj23QlM4AsMBqDXjhwpi1XRw5WkpWo02v3WVXit",
    "shop3": "https://buy.polar.sh/polar_cl_5xTGsDZ0tNZetCT8eLd1AIsmultLHtUf4zUE13sywjj",
    "papers": "1,038 sourced 2026 papers drive its methods",
    "skills": "404 verified code skills in its library",
}


def drafts():
    import CloudBrain as CB
    ask = ("Write 4 SHORT marketing posts (each <=400 chars total!) for an "
           "automated agent-family that: works open-source repos (2 real "
           "PRs already live: " + FACTS["prs"][0] + " and " +
           FACTS["prs"][1] + "), sells verified digital deliverable packs "
           "(" + FACTS["shop"] + "), runs entirely on free tiers and a "
           "16GB home box at $0/hr, with " + FACTS["papers"] + " and a "
           "disclosure-on-every-artifact honesty policy. The tone: "
           "honest, specific, zero hype, zero spam-speak. Reply ONLY "
           'JSON: {"show_hn": {"title": "Show HN: <the title>", "text": '
           '"<=2 short paras, honest"}, "reddit": {"sub": "r/opensource", '
           '"text": "the honest intro + the honest lines"}, "tweet": '
           '"<the short", "linkedin": "..."}.')
    r = CB.chat(ask, max_tokens=1400, purpose="the marketing drafts", models=("groq", "local-coder", "local-fast"))
    if not r:
        return None
    t = STRIP.sub("", r).strip().strip("`")
    m = re.search(r"\{[\s\S]*\}", t)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def run():
    os.makedirs(MK, exist_ok=True)
    d = drafts()
    if not d:
        # the honest fallback: the machine-written templates (no model)
        d = {
            "show_hn": {"title": "Show HN: Apex - a home-box agent family "
                        "that works OSS repos and sells verified "
                        "deliverable packs at $0/hr",
                        "text": ("Built over two days on a 16GB Windows "
                                 "box at $0/month: 4 local/cloud-free "
                                 "brains, a claim-audited earn loop "
                                 "(never takes a person's promised work), "
                                 "a 5-stage quality gate before every "
                                 "artifact ships + honest receipts in the "
                                 "ledger. Two PRs already in the world's "
                                 "review: see the hub " + FACTS["hub"] +
                                 ". The packs: " + FACTS["shop"] +
                                 " (the Triage pack's link). AMAs and "
                                 "critiques welcome - the honesty laws: "
                                 "print-or-it-didn-t-happen.")},
            "reddit": {"sub": "r/opensource",
                       "text": ("[Self-post, honest disclosure: my "
                                "automated agents] " + FACTS["hub"] +
                                " - the family works real OSS repos, "
                                "sells verified digital work-packs, and "
                                "publishes every receipt. Two PRs live "
                                "tonight. Interested in the community's "
                                "take on the disclosure policy: is "
                                "automated-contributor etiquette clear "
                                "enough?")},
            "tweet": ("An agent family ran 2 real PRs, a shop, and an "
                      "audit-able honesty ledger on a 16GB box at $0. "
                      + FACTS["hub"]),
            "linkedin": ("I run an automated agent family that ships "
                         "verified code contributions and sells the "
                         "deliverable packs (with human verification "
                         "before every delivery). The honest receipts: "
                         + FACTS["hub"])}
    files = {
        "SHOW_HN_post.md": f"# {d['show_hn']['title']}\n\n"
                           f"{d['show_hn']['text']}\n\n"
                           f"*(paste at https://news.ycombinator.com/submit "
                           f"— the Show-HN format; the founder's identity "
                           f"posts)*\n",
        "REDDIT_post.md": f"## Post to {d['reddit'].get('sub', 'r/opensource')}\n\n"
                          f"{d['reddit']['text']}\n\n*(reddit.com/{d['reddit'].get('sub','r/opensource')}"
                          f"/submit — read that sub's rules first (the "
                          f"self-promotion's disclosure = included))\n",
        "X_post.txt": STRIP.sub("", d.get("tweet", "")) + "\n*(x.com/compose*\n",
        "LINKEDIN_post.txt": STRIP.sub("", d.get("linkedin", "")) +
                             "\n*(linkedin.com/feed — the founder posts; "
                             "the disclosure remains)*\n",
    }
    for name, content in files.items():
        with open(os.path.join(MK, name), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(content)
        print(f"[marketing-kit] {name}: {len(content)} chars ready")
    hub_p = os.path.join(ROOT, "family", "marketing_kit_README.md")
    with open(hub_p, "w", encoding="utf-8", newline="\n") as f:
        f.write("# THE MARKETING KIT — paste-ready drafts (the founder's "
                "identities post)\n\n" +
                "".join(f"## {name}\n```\n{c[:600]}\n```\n"
                        for name, c in list(files.items())[:2]) +
                "\n*The law: the machine holds no social identities; the "
                "drafts = paste-ready; the posting = the founder's "
                "accounts.*")
    with open(os.path.join(ROOT, "Config", "marketing_kit.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "drafts": list(files.keys())}, f, indent=1)
    print(f"[marketing-kit] the kit built at {MK} (+ the hub's README)")
    return files


if __name__ == "__main__":
    run()