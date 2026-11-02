"""OutreachDraft - APEX'S CUSTOMER-CONTACT ORGAN (founder-gated).

The lawful channel = GitHub itself: a maintainer with an open, unanswered
call for help IS the potential customer; their issue thread = the contact
lane. This organ:
  1. SOURCES candidates: the scout feeds + a live help-wanted search ($0)
  2. DRAFTS the outreach per item - the deep brain, the HONEST template:
     who Apex is (autonomous peer, human-supervised), the observed need,
     a real proposed fix, the offer; zero invented claims; reply-anytime
  3. GATES: every draft lands in outreach_queue.jsonl (gate=FOUNDERS-CLICK).
     NOTHING is sent by this organ. One message per repo (dedupe ledger),
     ethically rate-limited (<=N/day), full disclosure, opt-out forever.
"""
import io
import json
import os
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain

K = CloudBrain.env_keys()
GH = K.get("GITHUB_TOKEN")
Q = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "scores")
sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
A = r"C:\Users\seaha\Apex-Adapter"
OUT = A + r"\outreach_queue.jsonl"
SENT_LEDGER = A + r"\outreach_sent.jsonl"
DAILY_CAP = 5                    # the anti-spam law
MAX_SEARCH = 4


def gh_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Apex-Outreach/1.0",
        "Accept": "application/vnd.github+json",
        **({"Authorization": "Bearer " + GH} if GH else {})})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def source_search():
    """live candidates: genuinely open help-wanted issues, small repos."""
    out = []
    try:
        d = gh_get('https://api.github.com/search/issues?q=type:issue+state:open+'
                   'label:"help+wanted"+created:%3E2026-10-26+is:not-pulled'
                   '&sort=created&per_page=6')
        for it in d.get("items", [])[:MAX_SEARCH]:
            out.append({"repo": it["repository_url"].split("repos/")[-1],
                        "issue": it["title"][:90],
                        "url": it["html_url"],
                        "body": (it.get("body") or "")[:400],
                        "source": "gh-helpwanted-live"})
    except Exception as e:
        print("[live-search FAIL]:", type(e).__name__, str(e)[:90])
    return out


def source_scouts():
    out = []
    try:
        with open(A + r"\bounty_drafts.jsonl", encoding="utf-8-sig") as f:
            seen = set()
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                key = d.get("repo", "") + "|" + d.get("issue", "")
                if key in seen:
                    continue
                seen.add(key)
                out.append({"repo": d.get("repo", "?"), "issue": d.get("issue", "?"),
                            "url": "gh-search", "body": "", "source": "scout-feed"})
    except Exception:
        pass
    return out


def cerebras_ask(item):
    import requests
    prompt = (f"Draft an HONEST, brief GitHub outreach message (<=120 words) to the "
              f"maintainer of repo '{item['repo']}'. Their open need: "
              f"'{item['issue']}'. Notes: {str(item.get('body',''))[:300]}. "
              "Rules: introduce Apex = an autonomous coding agent supervised by a human "
              "owner; state the OBSERVED need in one line; offer ONE concrete fix approach; "
              "NO invented results, NO claims of completed work; end with an easy "
              "'want a PR?' question. Plain text, no markdown headers.")
    lanes = [  # cross-PROVIDER drafting: cerebras, then groq (separate windows)
        ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY",
         "gpt-oss-120b"),
        ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY",
         "qwen-3.8-27b"),
        ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY",
         "openai/gpt-oss-120b"),
        ("https://api.siliconflow.com/v1/chat/completions", "SILICONFLOW_API_KEY",
         "Qwen/Qwen3.5-122B-A10B"),
    ]
    for attempt in range(2):
        for url, envk, model in lanes:
            key = K.get(envk)
            if not key:
                continue
            try:
                r = requests.post(
                    url, timeout=45,
                    headers={"Authorization": "Bearer " + key,
                             "Content-Type": "application/json",
                             "User-Agent": "Apex-Adapter/2.0"},
                    json={"model": model, "max_tokens": 350, "temperature": 0.3,
                          "messages": [{"role": "user", "content": prompt}]})
                if r.status_code == 200:
                    return (r.json()["choices"][0]["message"]["content"] or "").strip()
            except Exception:
                pass
        time.sleep(9)
    return None


def main():
    cands = source_search() + source_scouts()
    print("[candidates sourced]:", len(cands),
          "(", len([c for c in cands if c["source"].startswith("gh-")]), "live )")
    sent = set()
    if os.path.isfile(SENT_LEDGER):
        with open(SENT_LEDGER, encoding="utf-8-sig") as f:
            sent = {json.loads(l).get("repo") for l in f if l.strip()}
    today = time.strftime("%Y-%m-%d")
    drafted_today = 0
    if os.path.isfile(OUT):
        with open(OUT, encoding="utf-8-sig") as f:
            drafted_today = sum(1 for l in f
                                if l.strip() and json.loads(l).get("day") == today)
    n = 0
    queued_today = set()
    if os.path.isfile(OUT):
        with open(OUT, encoding="utf-8-sig") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    if d.get("day") == today:
                        queued_today.add(d.get("repo"))
    for c in cands:
        if c["repo"] in sent:
            continue
        if c["repo"] in queued_today:
            continue
        if drafted_today >= DAILY_CAP:
            print("[cap reached]:", DAILY_CAP, "drafts/day (anti-spam law)")
            break
        msg = cerebras_ask(c)
        rec = {**c, "message": msg or "(draft wall - judge window rested)",
               "day": today, "status": "FOUNDERS-CLICK",
               "credentials_sent": 0, "trap": None}
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        drafted_today += 1
        n += 1
        print(f"[drafted {n}] {c['repo'][:40]} | '{(msg or '')[:70]}...'")
    print("[queue]:", OUT, "| awaiting founder clicks; the organ NEVER sends.")


if __name__ == "__main__":
    main()