"""lane_benchmarks - THE NIGHTLY EVOLUTION ORGAN.

Runs 10 reference questions against every ALIVE brain (bench-aware, windows
polite), scores each answer against the reference with semantic Jaccard +
wall-time, and publishes the LEADERBOARD the seat map evolves from:

  scores/lane_scores.json  - raw per-lane results (committed to the repo)
  scores/leaderboard.md    - the ranked board (the evolution receipt)

Runs LOCALLY on a quiet-hour schedule (keys never leave the home - the
handoff law). $0 forever. The --quiet flag = scheduled mode (no chat).
"""
import io
import json
import os
import pathlib
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Scripts"))  # CloudBrain's home
import CloudBrain

K = CloudBrain.env_keys()
REPO = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCORES = REPO / "scores"
SCORES.mkdir(exist_ok=True)

REFS = [
    ("What is 17*23? Reply with the number only.", "391"),
    ("What is the capital of Australia? One word.", "Canberra"),
    ("Name the process plants use to make sugar from sunlight. Two words.",
     "photosynthesis"),
    ("What year did the Berlin Wall fall? Just the year.", "1989"),
    ("In one sentence: why does ice float on water?",
     "less dense"),
    ("What does HTTP status 429 mean? One short phrase.",
     "too many requests"),
    ("Spell the largest planet in our solar system. One word.",
     "Jupiter"),
    ("What language is primarily used for Android apps today? One word.",
     "Kotlin"),
    ("In one sentence: what is a mixture-of-experts model?",
     "routing through specialized expert"),
    ("Who wrote 'Crime and Punishment'? Last name only.", "Dostoevsky"),
]
LANES = [
    ("cerebras-120b", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "gpt-oss-120b", 60, 250),
    ("cerebras-qwen", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "qwen-3.8-27b", 60, 250),
    ("groq-120b", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b", 60, 400),
    ("groq-qwen", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "qwen/qwen3.8-27b", 60, 400),
    ("or-ultra", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b:free", 90, 400),
    ("sflow-122b", "https://api.siliconflow.com/v1/chat/completions",
     "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B", 90, 400),
    ("or-reason", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY",
     "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", 90, 500),
]
LEDGER = r"C:\Users\seaha\Apex-Adapter\lane_bench.json"


def jaccard(a, b, kws):
    toks = set(str(a).lower().replace(".", " ").replace(",", " ").split())
    if kws and all(k in toks for k in kws):
        return 1.0
    if kws and any(k in toks for k in kws):
        return 0.6
    B = set(str(b).lower().split())
    if not toks or not B:
        return 0.0
    return len(toks & B) / max(1, len(toks | B))


def main():
    try:
        ledger = json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        ledger = {}
    now = time.time()
    bench, results = [], {}
    for name, url, envk, model, tmo, mt in LANES:
        wall = ledger.get(name)
        if isinstance(wall, dict) and wall.get("until", 0) > now:
            results[name] = {"state": "resting",
                             "why": wall.get("why", ""), "score": None}
            print(f"{name:<16} resting - skipped honestly")
            continue
        key = K.get(envk)
        if not key:
            results[name] = {"state": "no-key", "score": None}
            print(f"{name:<16} no key - skipped")
            continue
        s, n, wall_s = 0.0, 0, 0.0
        for q, ref in REFS:
            kws = tuple(t for t in str(ref).lower().split("|")[0].split()
                        if len(t) > 2)
            try:
                t0 = time.time()
                import requests
                r = requests.post(
                    url, timeout=tmo,
                    headers={"Authorization": "Bearer " + key,
                             "Content-Type": "application/json",
                             "User-Agent": "Apex-Adapter/2.0"},
                    json={"model": model, "max_tokens": mt,
                          "messages": [{"role": "user", "content": q}]})
                wall_s += time.time() - t0
                if r.status_code == 200:
                    msg = r.json()["choices"][0]["message"]
                    s += jaccard(msg.get("content", ""), ref,
                                 kws if "one" in q.lower() or "spell" in q.lower()
                                 or "capital" in q.lower() else ())
                    n += 1
                elif r.status_code in (429, 402, 401, 403):
                    bench.append((name, f"HTTP {r.status_code}"))
                    break
                time.sleep(1.2)     # the organ-window politeness
            except Exception:
                continue
        if n:
            results[name] = {"state": "scored", "score": round(s / max(1, len(REFS)), 3),
                             "answered": n, "mean_wall_s": round(wall_s / n, 2)}
            print(f"{name:<16} score {results[name]['score']:.3f} "
                  f"({n}/10 answers, {results[name]['mean_wall_s']}s avg)")
        elif name in [b[0] for b in bench]:
            results[name] = {"state": "walled",
                             "why": dict(bench).get(name, ""), "score": None}
            print(f"{name:<16} walled honestly mid-bench")
        else:
            results[name] = {"state": "no-answers", "score": None}
            print(f"{name:<16} no answers scored")
    (SCORES / "lane_scores.json").write_text(json.dumps(
        {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "results": results}, indent=1),
        encoding="utf-8")
    ranked = sorted(((n, d["score"]) for n, d in results.items()
                     if d.get("score") is not None), key=lambda x: -x[1])
    lines = ["# The nightly leaderboard (the seat map evolves from this)",
             "", "**" + time.strftime("%Y-%m-%d %H:%M") + "**", ""]
    for n, s in ranked:
        d = results[n]
        lines.append(f"- **{s:.3f}** {n} — {d['answered']}/10 answered, "
                     f"{d['mean_wall_s']}s mean wall")
    (SCORES / "leaderboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[leaderboard]: " + ", ".join(f"{n}={s}" for n, s in ranked[:3]))
    if "--push" in sys.argv:
        for cmd in (["git", "add", "scores/"],
                    ["git", "commit", "-m", "scores: the nightly leaderboard [skip ci]"],
                    ["git", "fetch", "origin"], ["git", "pull", "--rebase", "origin", "main"],
                    ["git", "push"]):
            subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        REFS = REFS[:2]   # the 2-question proof (fast, few window-calls)
    main()