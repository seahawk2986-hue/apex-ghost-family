"""ArenaMini - the honest world-class scoreboard.

The law: "as good as the best agents" = a measured score on a public exam,
never a feeling. GSM8K = a standard frontier benchmark; Apex plays 30 of
its test problems, graded by the GI-gym's numeric-value truth law (no
string-shape charity). Free by construction: the exam = keyless GitHub
raw JSONL; the brains = the machine's own free lanes. Hardware-light:
short calls, sequential, no RAM spike.

Publishes scores/arena_mini.json + prints an honest verdict line.
score = answered-correct / samples; walls = lane refused (not scored).
"""
import io
import json
import os
import random
import re
import sys
import time
import urllib.request

import requests

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ENV = os.path.join(REPO, ".env")
OUT = os.path.join(REPO, "scores", "arena_mini.json")
EXAM_URL = ("https://raw.githubusercontent.com/openai/grade-school-math/"
            "master/grade_school_math/data/test.jsonl")
N = 30
SEED = 20261102

LANES = [
    ("groq-120b", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b"),
    ("groq-qwen", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "qwen/qwen3.8-27b"),
    ("cerebras-120b", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "gpt-oss-120b"),
    ("sflow-122b", "https://api.siliconflow.com/v1/chat/completions",
     "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B"),
    ("gemini-flash", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
     "GEMINI_API_KEY", "gemini-3.8-flash"),
    # the quota-FREE floor: local Ollama phi4-mini - never rate-capped, honest row
    ("local-phi4", "http://localhost:11434/v1/chat/completions",
     None, "phi4-mini:latest"),
]


def env_load():
    out = {}
    for ln in open(ENV, encoding="utf-8-sig"):
        if "=" in ln:
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def fetch_exam():
    req = urllib.request.Request(EXAM_URL, headers={"User-Agent": "apex-arena"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    items = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln:
            items.append(json.loads(ln))
    return items


def ask(env, url, key, model, question):
    prompt = (question + "\n\nSolve it step by step, briefly. "
              "End your reply with exactly: Final: <number>")
    headers = {"Content-Type": "application/json"}
    if key and env.get(key):
        headers["Authorization"] = "Bearer " + env[key]
    r = requests.post(url, headers=headers,
                      json={"model": model, "max_tokens": 1400,
                            "temperature": 0.0,
                            "messages": [{"role": "user", "content": prompt}]},
                      timeout=90)
    if r.status_code != 200:
        raise RuntimeError("HTTP " + str(r.status_code))
    msg = r.json()["choices"][0]["message"].get("content") or ""
    return msg


def model_number(text):
    m = re.findall(r"Final:?\s*\$?\s*(-?[\d,]*\.?\d+)", text)
    cand = m[-1] if m else None
    if cand is None:
        nums = re.findall(r"-?\d[\d,]*\.?\d*", text.replace("<think>", ""))
        cand = nums[-1] if nums else None
    try:
        return float(cand.replace(",", "")) if cand is not None else None
    except ValueError:
        return None


def gold_number(raw):
    g = raw.split("####")[-1].strip().replace(",", "").replace("$", "")
    return float(g)


def main():
    env = env_load()
    exam = fetch_exam()
    sample = random.Random(SEED).sample(exam, N)
    rows = []
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    for name, url, key, model in LANES:
        score, answered, walls = 0, 0, 0
        print(f"[lane]: {name} ({model})")
        for q in sample:
            time.sleep(2.5)  # the rate-politeness law: dodges the burst 429s
            gold = gold_number(q["answer"])
            text = None
            for attempt in (1, 2):
                try:
                    text = ask(env, url, key, model, q["question"])
                    walls = 0
                    break
                except Exception as e:
                    err = str(e)[:50]
                    if attempt == 1:
                        time.sleep(15)  # one honest retry after the cooldown
                        continue
                    walls += 1
                    print(f"   wall {err}")
            if text is None:
                if walls >= 2:
                    print("   [honest partial]: lane walled twice - stopping "
                          "this lane, no invented score")
                    break
                continue
            got = model_number(text)
            answered += 0 if got is None else 1
            if got is not None and abs(got - gold) < 1e-4:
                score += 1
        rows.append({"lane": name, "model": model,
                     "score": score, "answered": answered,
                     "walls": walls, "samples": len(sample)})
        pct = round(100.0 * score / len(sample), 1)
        gdy = round(100.0 * score / answered, 1) if answered else 0.0
        print(f"[{name}]: {score}/{len(sample)} ({pct}%) | answered {answered} "
              f"| accuracy-given-answer {gdy}% | walls {walls}")

    verdict = max(r["score"] for r in rows) if rows else 0
    doc = {"ts": ts, "exam": "gsm8k-test-30 (seed " + str(SEED) + ")",
           "truth_law": "numeric value, 1e-4", "results": rows,
           "best_score": verdict,
           "note": ("the score = Apex's measured lane accuracy; published "
                    "frontier-class exams run in the 90s of percent; this "
                    "number = the honest baseline the swarm/verify loops "
                    "must lift")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("[ledger]:", OUT)
    print(f"[verdict]: best lane = {verdict}/{N} measured, not claimed")


if __name__ == "__main__":
    main()