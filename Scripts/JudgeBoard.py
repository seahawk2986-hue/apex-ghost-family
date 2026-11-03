"""JudgeBoard - the job board's BRAIN (the find/label upgrade).

Every scouted draft gets a deep-brain verdict: fit / value / difficulty /
risk / verdict (file-now | verify-first | skip) + a one-line honest reason.
$0 lanes only (cerebras-120b primary 0.2s, cerebras-qwen reserve), bench-
aware, bounded calls. Output: scored board + the honest top pick.
The JSON-out uses the house extraction (fence -> last-brace), no model-judge
double-tax.
"""
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain

import requests

K = CloudBrain.env_keys()
URL = "https://api.cerebras.ai/v1/chat/completions"
H = {"Authorization": "Bearer " + K.get("CEREBRAS_API_KEY"),
     "Content-Type": "application/json",
     "User-Agent": "Apex-Adapter/2.0"}
A = r"C:\Users\seaha\Apex-Adapter"
DRAFTS = A + r"\bounty_drafts.jsonl"
SCORED = A + r"\bounty_scored.json"
MAX_CALLS = 6


def extract_json(text):
    text = text.strip()
    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.startswith("json"):
                p = p[4:]
            try:
                return json.loads(p)
            except Exception:
                pass
    s = text.find("{")
    if s != -1 and text.count("{") > text.count("}"):
        text = text[s:] + "}" * (text.count("{") - text.count("}"))
    try:
        return json.loads(text)
    except Exception:
        return None


def judge(item, n):
    prompt = ("You are a bounty triage judge. Judge this scouted open-source job:\n"
              "repo: " + item.get("repo", "?") + "\n"
              "issue: " + item.get("issue", "?") + "\n"
              "Reply ONLY compact JSON with keys fit(0-10), value(0-10), "
              "difficulty_hours(number), risk(0-10 false-positive odds), "
              "verdict(file-now|verify-first|skip), reason(one line).")
    time.sleep(3)                     # the window-politeness cure
    for attempt in range(2):          # one honest retry after a backoff
        for model in ("gpt-oss-120b", "qwen-3.8-27b"):
            try:
                t0 = time.time()
                r = requests.post(URL, headers=H, timeout=45,
                                  json={"model": model, "max_tokens": 300,
                                        "temperature": 0.1,
                                        "messages": [{"role": "user",
                                                      "content": prompt}]})
                dt = round(time.time() - t0, 2)
                if r.status_code == 200:
                    d = extract_json(r.json()["choices"][0]["message"]["content"])
                    if isinstance(d, dict):
                        d["judged_by"] = model
                        d["judge_s"] = dt
                        return d
            except Exception:
                pass
        if attempt == 0:
            time.sleep(9)             # the flapping-window backoff
    return {"verdict": "unjudged", "reason": "no alive judge brain"}


def main():
    items = []
    with open(DRAFTS, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    print("[drafts to judge]:", len(items))
    out, calls = [], 0
    for i, item in enumerate(items):
        if calls >= MAX_CALLS:
            out.append({**item, "judge": {"verdict": "bounded",
                                          "reason": "call cap (honest)"}})
            continue
        j = judge(item, i)
        calls += 1
        out.append({**item, "judge": j})
        print(f"  [{i}] {item.get('issue','?')[:44]} -> "
              f"{j.get('verdict')} fit={j.get('fit')} val={j.get('value')} "
              f"risk={j.get('risk')} | {str(j.get('reason',''))[:60]}")
    with open(SCORED, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "judged": out}, f,
                  ensure_ascii=False, indent=1)
    ranked = sorted((o for o in out if isinstance(o.get("judge"), dict)
                     and o["judge"].get("verdict") not in ("unjudged", "bounded")),
                    key=lambda o: -(o["judge"].get("fit", 0)
                                    + o["judge"].get("value", 0)
                                    - o["judge"].get("risk", 0)))
    if ranked:
        top = ranked[0]
        print("[TOP PICK]:", top.get("repo"), "—", top.get("issue"),
              "| verdict:", top["judge"].get("verdict"),
              "| reason:", str(top["judge"].get("reason", ""))[:90])
    print("[scored board]:", SCORED, "| judge calls:", calls)


if __name__ == "__main__":
    main()