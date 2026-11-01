"""GH ARCHIVE LANE (doctrine Part V, K4/K6#1): the entire public GitHub
timeline as HOURLY JSON.GZ dumps at data.gharchive.org - keyless, no rate
limit, no API budget. This lane pulls recent hours, mines repo leads from
PushEvent (OctoPack's unit: commits pair work with intent, K1) and feeds the
bug lane from good-first-issue labels (GFI pattern, K4).
STANDALONE by design: no SwarmOrchestrator imports - the orchestrator wires
this lane in AFTER the marathon. RAM ~ streaming light; bounded buffers.

HONESTY: every step prints its counts; a bad hour is skipped loudly; the
leads file is APPEND-ONLY JSONL with evidence roots (source, hour url)."""
import gzip
import io
import json
import os
import time
import urllib.request

AD = r"C:\Users\seaha\Apex-Adapter"
LEADS = os.path.join(AD, "gh_archive_leads.jsonl")
BUGS = os.path.join(AD, "gh_archive_bugs.jsonl")
STATE = os.path.join(AD, "swarm_state.json")
_GFI = ("good first issue", "good-first-issue", "help wanted")


def _hour_url(dt):
    return "https://data.gharchive.org/" + dt.strftime("%Y-%m-%d-%H") + ".json.gz"


def _seen_repos():
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
        return set(st.get("repos", [])), set(st.get("pending_leads", []))
    except Exception:
        return set(), set()


def pull(hours_back=2, max_leads=400, max_bugs=40, per_owner=5):
    """Pull the last `hours_back` hourly archives (skip the in-progress one),
    stream-filter, and append leads + bug candidates. Prints every count."""
    stats = {"hours": 0, "bytes": 0, "events": 0, "push_repos": 0,
             "leads": 0, "bug_candidates": 0}
    seen, queued = _seen_repos()
    owner_count = {}
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    for h in range(1, hours_back + 1):
        dt0 = (now - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
        url = _hour_url(dt0)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
            stats["bytes"] += len(raw)
            stats["hours"] += 1
        except Exception as e:
            print(f"[gh-archive] hour {dt0:%Y-%m-%d-%H} failed: {str(e)[:60]} - skipped loudly")
            continue
        gz = gzip.GzipFile(fileobj=io.BytesIO(raw))
        n_new = n_bugs = n_ev = 0
        with open(LEADS, "a", encoding="utf-8") as lf, \
             open(BUGS, "a", encoding="utf-8") as bf:
            for line in io.TextIOWrapper(gz, encoding="utf-8", errors="ignore"):
                if not line.strip():
                    continue
                stats["events"] += 1
                n_ev += 1
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                repo = (ev.get("repo") or {}).get("name", "")
                typ = ev.get("type", "")
                if not repo or "/" not in repo:
                    continue
                owner = repo.split("/")[0]
                if typ == "PushEvent" and repo not in seen and repo not in queued:
                    if owner_count.get(owner, 0) >= per_owner:   # diversity guard
                        continue
                    n_new += 1
                    stats["push_repos"] += 1
                    owner_count[owner] = owner_count.get(owner, 0) + 1
                    lf.write(json.dumps({"repo": repo, "source": "gh-archive",
                                         "hour": dt0.strftime("%Y-%m-%d-%H"),
                                         "ts": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
                elif typ in ("IssuesEvent", "IssueLabelEvent"):
                    labels = " ".join(str((l or {}).get("name", ""))
                                      for l in (ev.get("payload", {}).get("issue", {})
                                                or {}).get("labels", []) or [])
                    if any(g in labels.lower() for g in _GFI):
                        n_bugs += 1
                        stats["bug_candidates"] += 1
                        if n_bugs <= max_bugs:
                            bf.write(json.dumps({"repo": repo,
                                                 "issue": (ev.get("payload", {})
                                                           .get("issue", {}) or {}).get("title",
                                                                                        "")[:100],
                                                 "source": "gh-archive-gfi",
                                                 "ts": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
        stats["leads"] += n_new
        print(f"[gh-archive] {dt0:%Y-%m-%d-%H}: {n_ev:>6} events -> +{n_new} leads, "
              f"+{n_bugs} gfi-bug candidates (MB: {len(raw)//2**20})")
        if stats["leads"] >= max_leads:
            print("[gh-archive] lead cap reached - remaining hours left for the next pull")
            break
    print(f"[gh-archive] TOTAL: {stats['hours']} hours, {stats['events']} events, "
          f"{stats['leads']} new leads, {stats['bug_candidates']} gfi-bug candidates "
          f"({stats['bytes'] // 2**20} MB pulled) - every count printed, nothing claimed")
    return stats


if __name__ == "__main__":
    import sys
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    pull(hours_back=hrs)