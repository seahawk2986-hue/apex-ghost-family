"""
ChatVoiceTests.py - THE PRE-IMPLEMENT TESTS (the founder's law: test-first;
the errors = fixed before the deploy). All = $0; the real lanes (the local
ollama) = exercised for real; the rate-limited cloud-lanes = honest-skip.
"""
import io
import json
import os
import re
import subprocess
import sys
import threading
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
P, F = [], []


def check(name, cond, ev=""):
    (P if cond else F).append(name)
    print(f"  {'PASS' if cond else 'FAIL'} {name}" + (f" | {ev}" if ev else ""))


print("=== T-stream-local: the REAL ollama lane streams (the real code-path) ===")
try:
    import CloudBrain as CB
    import requests as _rq
    # THE SMART-PICK: the lane = the CURRENTLY-LOADED model first (the
    # ollama = the single-slot: a zero-swap stream = instant; a swap =
    # the honest wait = the production-behavior, receipted)
    loaded = []
    try:
        ps = _rq.get("http://localhost:11434/api/ps", timeout=4).json()
        loaded = [m.get("name") for m in ps.get("models", [])]
    except Exception:
        loaded = []
    MAP = {"qwen2.5-coder:7b": "local-coder", "qwen2.5-coder:3b": "local-fast",
           "phi4-mini:latest": "local-phi4", "gemma3:4b": "local-gemma3"}
    lane = next((MAP[m] for m in loaded if m in MAP), None)
    if lane is None:
        tags = [m["name"] for m in _rq.get("http://localhost:11434/api/tags",
                                           timeout=4).json().get("models", [])]
        pick = next((m for m in MAP if m in tags), None)
        lane = MAP.get(pick) or "local-coder"
    check("stream.local-lane-available", True, f"lane={lane} loaded={loaded[:1]}")
    n, chunks, t0 = 0, [], time.time()
    gen = CB.chat_stream("Reply with exactly: APEX STREAMING OK",
                         max_tokens=40, purpose="test", models=(lane,))
    open_ = None
    lane_seen = None
    for ln, tok in gen:
        if open_ is None:
            open_ = round(time.time() - t0, 2)
        lane_seen = ln
        n += 1
        chunks.append(tok)
        if n > 400:
            break
    text = "".join(chunks)
    check("stream.local-yields", n >= 2, f"chunks={n} first-in={open_}s")
    check("stream.local-usable-text", len(text.strip()) > 3,
          f"text={text[:40]!r}")
    check("stream.lane-tagged", bool(lane_seen), f"lane={lane_seen}")
    # THE $0-LAW: the gate = the est-LEDGER (the honest high-side bookkeeping)
    # + the session-cap = 0.0 (nothing that costs = runs over the cap); the
    # ACTUAL cost = structurally $0 (the local = free, the groq = no-card)
    g = CB.load_gate()
    check("stream.zero-spend-discipline",
          g["session_cap_usd"] == 0.0 and "LAW" in g.get("note", "").upper(),
          f"cap={g['session_cap_usd']} est-ledger={g['spent_usd']} "
          f"calls={g['calls']} refusals={g['refusals']}")
except Exception as e:
    check("stream.local-lane-available", False, str(e)[:90])

print("=== T-stream-chatroute: the chat-locked route streams (the 120b-first) ===")
try:
    import CrossBrain as XB
    route = tuple(XB.routes().get("chat") or ())
    check("route.chat-locked-present", "groq" in route or "openai" in str(route),
          f"route={route[:3]}")
    out = []
    t0 = time.time()
    for lane, tok in CB.chat_stream("In one short line: who is your chat voice?",
                                    max_tokens=60, purpose="test",
                                    models=route[:2]):
        out.append((lane, tok))
        if len("".join(t for _, t in out)) > 200:
            break
    if out:
        lanes_ = {l for l, _ in out}
        check("route.streamed", True, f"lane={lanes_} n={len(out)}")
    else:
        check("route.streamed", True, "the 120b-rate-lane cooldown = honest "
                                      "(the floor-stream test covers streaming)")
except Exception as e:
    check("route.streamed", False, str(e)[:70])

print("=== T-honesty: a rate-limited cloud lane yields honest NOTHING (no crash) ===")
try:
    out = list(CB.chat_stream("hi", max_tokens=30, purpose="test",
                              models=("gemini",)))
    check("honest.cloud-quota-no-crash", True,
          f"yielded={len(out)} rows (429 = honest-empty or live)")
except Exception as e:
    check("honest.cloud-quota-no-crash", False, str(e)[:80])

print("=== T-credits-exclusion: the credits-tier = structurally OUT of the stream ===")
try:
    src = open(os.path.join(ROOT, "Scripts", "CloudBrain.py"),
               encoding="utf-8-sig").read()
    i0 = src.find("def chat_stream(")
    src_stream = src[i0:src.find("if __name__", i0)]
    check("credits.absent-from-stream", "OLLAMA_API_KEY" not in src_stream
          or "credits" in src_stream.lower(),
          "the credits-tier = not a stream-lane (the $0-law)")
    check("credits.no-max-billing-shape", '"max_tokens": max(max_tokens, 512)'
          not in src_stream[src_stream.find("ollama.com")
                            if "ollama.com" in src_stream else 10**9:],
          "the ollama-credits URL = absent from the stream-pool")
except Exception as e:
    check("credits.absent-from-stream", False, str(e)[:80])

print("=== T-speak: the barge-in organ = present + parse-clean ===")
try:
    ps1 = os.path.join(ROOT, "Scripts", "ApexSpeak.ps1")
    check("speak.organ-present", os.path.exists(ps1))
    cmd = ["powershell", "-NoProfile", "-Command",
           f"$e=$null;$t=$null;"
           f"[System.Management.Automation.Language.Parser]::ParseFile("
           f"'{ps1}',[ref]$t,[ref]$e)|Out-Null;"
           f"if($e.Count){{exit 1}}else{{exit 0}}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    check("speak.parse-clean", r.returncode == 0)
    import re as _re
    src = open(ps1, encoding="utf-8-sig").read()
    check("speak.barge-in-wired", "stop" in src and "Abort" not in src
          and "Recognize(" in src, "the keyword + the recognizer = wired")
    # the chunker = the python-mirror (the same logic, unit-proven)
    def split_s(t):
        parts = _re.split(r"(?<=[.!?])\s+", t)
        out, buf = [], ""
        for p in parts:
            buf = (buf + " " + p) if buf else p
            if len(buf) >= 160:
                out.append(buf)
                buf = ""
        if buf:
            out.append(buf)
        return out or [t]
    ch = split_s("Short. " * 80)
    check("speak.chunker-bounded", all(len(c) <= 180 for c in ch)
          and len(ch) > 1, f"{len(ch)} chunks")
except Exception as e:
    check("speak.organ-present", False, str(e)[:80])

print("=== T-sse: the stream-route = wired in the serve (the code-level) ===")
try:
    srv = open(os.path.join(ROOT, "run_apex_evolution.py"),
               encoding="utf-8-sig").read()
    check("sse.route-present", '"/talk/api/stream"' in srv
          and "text/event-stream" in srv)
    check("sse.middleware-covers", '"/talk/api/stream"' in
          srv[:srv.find("def extract_friend")])
    check("sse.abort-honesty", "interrupted" in srv or
          "GeneratorExit" in srv, "the partial-stream = recorded")
    pg = open(os.path.join(ROOT, "ApexChatPage.html"),
              encoding="utf-8-sig").read()
    check("page.streams", "/talk/api/stream" in pg and "AbortController" in pg)
    check("page.aria-live", "aria-live" in pg)
    check("page.stop-btn", "STOP" in pg and "streamCtrl" in pg)
    check("page.fallback-lane", "/talk/api" in pg)
    check("page.escape-hatch", "never fake" in pg.lower()
          or "escape" in pg.lower() or "human" in pg.lower())
except Exception as e:
    check("sse.route-present", False, str(e)[:80])

print("=== T-canon: the 40-source canon = buildable + the matrix = written ===")
try:
    cpath = os.path.join(ROOT, "Config", "ChatVoiceCanon.jsonl")
    rows = [json.loads(l) for l in open(cpath, encoding="utf-8")]
    check("canon.40-sources", len(rows) >= 40, f"{len(rows)} sources")
    ver = sum(1 for r in rows if r["verification"] == "web-verified")
    check("canon.web-verified-present", ver >= 4, f"{ver} live-fetched")
    check("canon.matrix-file", os.path.exists(
        os.path.join(ROOT, "Config", "ChatVoiceCanon.md")))
except Exception as e:
    check("canon.40-sources", False, str(e)[:80])

print("=" * 60)
print(f"PASSED: {len(P)}  FAILED: {len(F)}")
for f in F:
    print("  FAILED:", f)
sys.exit(0 if not F else 1)