"""WebUse - THE WEB-USE ORGAN (the A+ round, 2026-11-04).

THE SCORED GAP (the verified frontier scorecard): computer/web use was the
D- axis - scrapers existed, but no browse-read-ANSWER organ with receipts.
THE DOCTRINE (the outsource law): the HOST fetches only (stdlib urllib,
bounded, polite); the UNDERSTANDING is outsourced to the fleet's FREE
lanes ($0) - so the 16GB box spends ~0 RAM on web work. The verified
mini-swe-agent lesson applies here too: minimal scaffolding, the model
does the work, the RECEIPT is the proof.

CAPABILITIES (honest tiers):
  fetch(url)              - bounded polite GET -> raw text/html (receipted)
  read(url, ask)          - fetch + free-lane comprehension -> sourced answer
  selftest()              - verify against a REAL live URL (raw.githubusercontent)
                            - the receipt: a question ANSWERED from the web,
                              lane-tagged, $0 - external evidence, print-first.

Every row lands in Scores/web_use.jsonl: {ts, op, url, ok, lane, wall_s,
note}. Bounded: 500KB body cap, 15s timeouts, 1 retry max. Fail-closed:
a dead lane returns honestly; never invents a fetched byte.
"""
import html.parser
import json
import os
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(ROOT, "Scores", "web_use.jsonl")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))

UA = {"User-Agent": "apex-webuse/1.0 (the family's web-use organ; polite, bounded)"}
BODY_CAP = 500 * 1024


class _Text(html.parser.HTMLParser):
    """Stdlib html->text (no bs4 needed: the fetch stays dependency-free)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._out = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("p", "div", "br", "li", "h1", "h2", "h3", "tr"):
            self._out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self._out.append(data)


def _log(op, url, ok, lane, t0, note=""):
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "op": op, "url": url[:300],
           "ok": bool(ok), "lane": lane, "wall_s": round(time.time() - t0, 1),
           "note": str(note)[:200]}
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return row


def fetch(url):
    """Bounded, polite fetch -> {ok, text, bytes, note}. Never raises."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(BODY_CAP + 1)
        if len(raw) > BODY_CAP:
            raw = raw[:BODY_CAP]
        text = raw.decode("utf-8", errors="replace")
        return _log("fetch", url, True, "stdlib", t0, f"{len(raw)} bytes") | \
            {"text": text}
    except Exception as e:
        out = _log("fetch", url, False, "stdlib", t0, f"{type(e).__name__}: {str(e)[:90]}")
        return out | {"text": ""}


def _strip_html(raw):
    p = _Text()
    try:
        p.feed(raw)
        return " ".join("".join(p._out).split())[:24000]
    except Exception:
        return raw[:24000]


def read(url, question):
    """The web-QA: fetch url -> outsource comprehension to the free lanes ->
    a sourced answer (the lane is named; $0; honest NOT FOUND if the page
    does not contain it)."""
    t0 = time.time()
    got = fetch(url)
    if not got.get("ok"):
        return _log("read", url, False, "no-fetch", t0, got.get("note", "")) | \
            {"answer": "FETCH FAILED (honest)", "url": url}
    body = _strip_html(got.get("text", ""))
    if not body:
        return _log("read", url, False, "no-text", t0, "empty after strip") | \
            {"answer": "PAGE EMPTY (honest)", "url": url}
    prompt = (
        "You are Apex's web-reading lane. Answer the QUESTION using ONLY the page "
        "text below. If the answer is not in the page, reply exactly: NOT IN PAGE.\n"
        f"QUESTION: {question}\n\nPAGE ({url}):\n{body[:12000]}\n\n"
        "ANSWER (one or two sentences, cite the page fact):")
    lane = "unknown"
    answer = ""
    try:
        import CloudBrain as CB
        # THE OUTSOURCE-THE-EYES law + the strength chain: web reading = the
        # strongest FREE lanes in strength order (gemini VL-class -> 120b ->
        # the titans -> the swarm rotator); the LOCAL floor is never in this
        # route (its RAM stays for the chat; its web-reading = the weak seat)
        answer = CB.chat(prompt, max_tokens=250, purpose="webuse read",
                         models=("gemini", "groq", "nim-glm", "nemotron-550b",
                                 "or-swarm")) or ""
        import json as _j
        try:
            lanes = _j.load(open(os.path.join(ROOT, "scores", "lane_state.json"),
                                 encoding="utf-8-sig")) if os.path.exists(
                os.path.join(ROOT, "scores", "lane_state.json")) else {}
        except Exception:
            lanes = {}
        lane = "free-lanes(fleet)"
    except Exception as e:
        answer = f"lane fail: {type(e).__name__}"
    ok = bool(answer) and "NOT IN PAGE" not in answer and "lane fail" not in answer
    return _log("read", url, ok, lane, t0, "" if ok else answer[:120]) | \
        {"answer": (answer or "")[:500], "url": url}


def selftest():
    """THE EXTERNAL RECEIPT: one REAL live-URL question answered. The check
    = an independently verifiable fact from a raw.githubusercontent file."""
    r = read("https://raw.githubusercontent.com/SWE-agent/mini-swe-agent/main/README.md",
             "What percentage score does the SWE-bench verified benchmark claim in the README?")
    ans = (r.get("answer") or "").lower()
    r["external_check"] = "passed" if "74" in ans else ("failed: " + ans[:120])
    print(json.dumps({k: r.get(k) for k in ("ok", "lane", "wall_s",
                                            "external_check")},
                     ensure_ascii=False))
    return r


if __name__ == "__main__":
    print(json.dumps(selftest(), indent=1, ensure_ascii=False)[:1200])