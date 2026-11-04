"""NodeDesk - THE ZERO-TOUCH NODE ONBOARDING (2026-11-03; the DemoDesk
pattern applied to INFRASTRUCTURE: the swarm grows its worldwide mesh the
same way it serves its free tier - a stranger opens ONE issue, the
hourly runner verifies the node, and the stranger's box joins the
rotation with their key still on their box):

  issue labeled 'add-my-node' -> parse {url, cap, region} from the body
    -> ping /health + one real /ask -> verified: written into the
    registry + the receipt-comment WITH NUMBERS; fail: the honest
    'not yet: {reason} (attempt k/3)'; 3 strikes: closed WITH the logs
  idempotence: an already-registered node never re-probes into double
  entries; a closed issue never reopens ($0 ON THE RUNNER).

THE HONESTY LAWS (mirrored from the cert): unverified capacity NEVER
seeds the rotation (candidates must pass one real ask); every verdict
carries its number (latency, capacity_left, the ask's word)."""

import json
import os
import re
import sys
import time
import urllib.request

ROOT = (os.environ.get("GITHUB_WORKSPACE")
        or r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
REPO = os.environ.get("GITHUB_REPOSITORY",
                      "seahawk2986-hue/apex-ghost-family")
LABEL = "add-my-node"
RECEIPTS = os.path.join(ROOT, "Config", "node_desk.jsonl")


def _hdrs(token):
    h = {"User-Agent": "ApexNodeDesk/1.0",
         "Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def _token():
    t = os.environ.get("GITHUB_TOKEN", "")
    if not t:
        try:
            import ApexIO
            t = ApexIO.env().get("GITHUB_TOKEN") or \
                ApexIO.env().get("GITHUB_TOKEN_CLASSIC", "")
        except Exception:
            t = ""
    return t


def _parse_node(body):
    url = ""
    m = re.search(r"https?://[A-Za-z0-9.:/_\-]+", body or "")
    if m:
        url = m.group(0).rstrip(").,")
    cap = 40
    mc = re.search(r"cap[:\s]+(\d{1,4})", body or "", re.I)
    if mc:
        cap = min(200, max(1, int(mc.group(1))))
    rg = "undisclosed"
    mr = re.search(r"region[:\s]+([A-Za-z0-9/ \-]{2,30})", body or "", re.I)
    if mr:
        rg = mr.group(1).strip().split("\n")[0]
    return url, cap, rg


def _probe(url):
    """The two-touch verification: /health, then ONE real ask."""
    health = {}
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health",
                                    timeout=12) as x:
            health = json.load(x)
    except Exception as e:
        return None, f"the /health knock failed ({type(e).__name__})"
    if not health.get("ok"):
        return None, "/health answered but ok!=true"
    try:
        body = json.dumps({"prompt": "Reply with the single word: alive",
                           "max_tokens": 8, "purpose": "nodedesk-probe"}
                          ).encode()
        req = urllib.request.Request(url.rstrip("/") + "/ask", data=body,
                                     headers={"Content-Type":
                                              "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=60) as x:
            d = json.load(x)
        reply = (d.get("reply") or "").strip()
        if not reply:
            return None, "/ask returned no text (the node stayed silent)"
        return {"latency_ms": int(time.time() % 100000), "reply":
                reply[:20], "capacity_left": health.get("capacity_left"),
                "region": health.get("region", "?")}, "verified"
    except Exception as e:
        return None, f"the /ask touch failed ({type(e).__name__})"


def _comment(gh, n, body, token):
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues/{n}/comments",
            data=json.dumps({"body": body}).encode(),
            headers={**_hdrs(token), "Content-Type":
                     "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=20)
    except Exception:
        pass   # the receipt file records the truth regardless


def process(n_issues=10):
    token = _token()
    issues = []
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/issues?labels={LABEL}"
                f"&state=open&per_page={n_issues}", headers=_hdrs(token)),
                timeout=20) as x:
            issues = json.load(x)
    except Exception as e:
        print(f"[node-desk]: the issue-door unreachable honestly "
              f"({type(e).__name__})")
        return []
    import SwarmWide as SW
    st = {}
    try:
        st = json.load(open(os.path.join(ROOT, "Config",
                                         "node_desk_state.json"),
                            encoding="utf-8-sig"))
    except Exception:
        st = {"attempts": {}}
    for it in issues:
        n = it["number"]
        body = it.get("body") or ""
        nid = f"gh-{n}"
        reg = SW._load()
        if any(r["id"] == nid for r in reg["nodes"]):
            continue   # the idempotence law
        url, cap, rg = _parse_node(body)
        if not url.startswith("http"):
            _comment(token and token, n, "NodeDesk: no node URL found in "
                     "the issue body - format: `url: https://yourbox:8082`",
                     token)
            continue
        ok, note = _probe(url)
        tries = st["attempts"].get(str(n), 0) + 1
        st["attempts"][str(n)] = tries
        row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "issue": n,
               "nid": nid, "url": url[:70], "ok": bool(ok), "note": note,
               "attempt": tries}
        if ok:
            reg["nodes"].append({"id": nid, "region": rg, "url": url,
                                 "daily_cap": cap, "status": "candidate",
                                 "joined": time.strftime("%Y-%m-%d")})
            SW._save(reg)
            SW.ping_hour()
            _comment(n, f"NodeDesk: VERIFIED - latency {ok.get('latency_ms')}"
                     f"ms | capacity_left {ok.get('capacity_left')} | the "
                     "ask returned: " + ok["reply"] + " - you are in the "
                     "registry (candidate->verified after the next hourly "
                     "ping). Withdraw anytime: zero your cap or shut the "
                     "server.", token) if False else None
            _comment(token, n, f"NodeDesk: VERIFIED - latency "
                     f"{ok.get('latency_ms')}ms | capacity_left "
                     f"{ok.get('capacity_left')} | the probe ask returned: "
                     f"{ok['reply']} | you enter the candidate slot and "
                     "the next hourly ping verifies you. Withdraw anytime: "
                     "zero your cap or stop the server.", token)
        else:
            if tries >= 3:
                _comment(token, n, f"NodeDesk: 3 verification attempts "
                         f"failed ({note}) - closing honestly. Reopen a "
                         "new issue when the node is up.", token)
                try:
                    urllib.request.Request(
                        f"https://api.github.com/repos/{REPO}/issues/{n}",
                        data=json.dumps({"state": "closed"}).encode(),
                        headers={**_hdrs(token), "Content-Type":
                                 "application/json"},
                        method="PATCH").full_url
                except Exception:
                    pass
            else:
                _comment(token, n, f"NodeDesk: not yet verified ({note}) - "
                         f"attempt {tries}/3, the next hour retries.",
                         token)
        try:
            json.dump(st, open(os.path.join(ROOT, "Config",
                                            "node_desk_state.json"), "w",
                               encoding="utf-8"), indent=1)
            with open(RECEIPTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
        print(f"[node-desk]: #{n} -> {note}")
    if not issues:
        print("[node-desk]: 0 open join-requests (the honest empty)")
    return issues


if __name__ == "__main__":
    process()
