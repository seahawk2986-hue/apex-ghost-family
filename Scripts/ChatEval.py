"""CHATEVAL: the BLIND A/B/C/D race across the roster's chat-lanes;
the gpt-oss-120b (via groq) judges anonymized answers; the ranks receipted
-> the hybrid_routes' CHAT-lane = the DATA-driven (the routes learn!).
The serial one-at-a-time = the RAM-law (the ollama's single-slot swap).
$0.00 always."""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.environ.get("APEX_ROOT",
                      r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))

LANES = [
    ("groq-120b", None, "groq"),
    ("qwen25-7b", "qwen2.5-coder:7b", None),
    ("phi4-mini", "phi4-mini:latest", None),
    ("deepseek-r1", "deepseek-r1:7b", None),
]
ASKS = [
    "Explain in <=120 words what an 'agent family' does for an OSS repo.",
    "A client asks: is my data safe if I send you a repo link? Answer "
    "honestly, <=100 words.",
    "Rewrite this sentence to be specific not hype: 'We are "
    "revolutionizing automation.'",
]


def ask_local(model, prompt):
    r = subprocess.run(["ollama", "run", model, prompt],
                       capture_output=True, text=True, timeout=420,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def ask_groq(prompt):
    sys.path.insert(0, os.path.join(ROOT, "Scripts"))
    from CloudBrain import env_keys
    import urllib.request
    k = env_keys().get("GROQ_API_KEY", "")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({"model": "openai/gpt-oss-120b",
                         "messages": [{"role": "user", "content": prompt}],
                         "temperature": 0.2, "max_tokens": 350}).encode(),
        headers={"Authorization": "Bearer " + k,
                 "Content-Type": "application/json",
                 "User-Agent": "apex-chat/1.0"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    return (d.get("choices") or [{}])[0].get("message", {}).get("content",
                                                                "").strip()


def main():
    evalout = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "asks": []}
    for ai, a in enumerate(ASKS):
        answers = {}
        for lane, model, kind in LANES:
            try:
                answers[lane] = (ask_groq(a) if kind else
                                 ask_local(model, a))[:900]
            except Exception as e:
                answers[lane] = ""
                evalout.setdefault("errs", []).append(
                    f"{lane}/ask{ai}: {str(e)[:60]}")
        served = {k: v for k, v in answers.items() if v.strip()}
        if len(served) < 2:
            evalout["asks"].append({"n": ai, "verdict": "HONEST-SKIP (the "
                                    "lanes' outage)", "served": len(served)})
            continue
        # the BLIND pack
        letters = list("ABCD")[:len(served)]
        pack = "\n\n".join(f"Answer {L}:\n{served[k]}"
                           for L, k in zip(letters, served))
        names = list(served.keys())
        j = None
        try:
            j = ask_groq('You judge anonymized answers for a chat-lane. '
                         "Question " + str(ai + 1) + ". " + a +
                         "\n\n" + pack + "\n\nRank ALL answers best-to-"
                         'worst for honesty+clarity+specificity. Reply '
                         'ONLY JSON: {"rank": ["A", "B"], "why": "<=140 '
                         'chars"}')
        except Exception:
            pass
        m = re.search(r"\{[\s\S]*\}", (j or ""))
        try:
            jd = json.loads(m.group(0)) if m else {}
        except Exception:
            jd = {}
        evalout["asks"].append({"n": ai, "lanes": names, "rank":
                                jd.get("rank", []), "judge_why":
                                jd.get("why", "")[:140], "count":
                                len(served)})
        print(f"[chat-eval] the ask {ai + 1}: served {len(served)} | "
              f"judge -> {jd.get('rank', 'x')}")
        time.sleep(2)
    with open(os.path.join(ROOT, "Config", "chat_eval.json"), "w",
              encoding="utf-8") as f:
        json.dump(evalout, f, ensure_ascii=False, indent=1)
    # the route-learning: the ranks -> the chat-lane's order (the DATA!)
    tally = {}
    for x in evalout["asks"]:
        for pos, L in enumerate(x.get("rank") or []):
            if L in dict(zip(x.get("lanes", []), letters)):
                name = x["lanes"][list(x["lanes"]).index(L)]
                tally[name] = tally.get(name, 0) + (10 - pos)
    order = [k for k, _ in sorted(tally.items(), key=lambda kv: -kv[1])]
    if order:
        rp = os.path.join(ROOT, "Config", "hybrid_routes.json")
        try:
            routes = json.load(open(rp, encoding="utf-8-sig"))
        except Exception:
            routes = {}
        routes["chat"] = order
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(routes, f, ensure_ascii=False, indent=1)
        print(f"[chat-eval] THE ROUTE LEARNED: chat -> {order}")


if __name__ == "__main__":
    main()