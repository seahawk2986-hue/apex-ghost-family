"""MoneyCompare - restored (the same organ: the 10-way patterns judged vs Apex)."""
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain
import requests

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
MONEY = os.path.join(REPO, "money")
K = CloudBrain.env_keys()
APY = {
    "has": ["tiered multi-brain chat", "swarm consensus on deep turns",
            "durable room memory", "GI gym + 435-skill library + SkillEvolve",
            "job-board scout + JudgeBoard (file-now verdicts)",
            "founder-gated outreach drafts + claim-audit off-box",
            "Polar rails live ($200/$150/$75 products)",
            "V2 coding engine containerized - pending acceptance",
            "all $0-spends, RAM-gated"],
    "laws": ["Apex never SPENDS money (incoming = the goal)",
             "keys stay home; no invented approvals/claims; anti-spam"]}


def collect():
    pats = {}
    for n in range(1, 11):
        p = os.path.join(MONEY, f"pass-{n}", "wave.md")
        if not os.path.isfile(p):
            continue
        head = open(p, encoding="utf-8").read()
        pline = [l for l in head.splitlines() if l.startswith("patterns:")]
        for s in (pline[0][len("patterns:"):].split(",") if pline else []):
            s = s.strip()
            if s:
                pats.setdefault(s, {"passes": []})
                pats[s]["passes"].append(n)
    return pats


def judge(name, meta):
    prompt = ("Judge: self-improving agent 'Apex' has: "
              + "; ".join(APY["has"][:5]) + ". Laws: " + "; ".join(APY["laws"])
              + ". The proven mechanism: '" + name + "'. Smallest concrete build? "
              "Reply ONLY JSON: verdict(IMPROVE-NOW|BUILD-NEXT|NOT-APPLICABLE), "
              "build(<=25 words), reason(one line).")
    lanes = [("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY", "gpt-oss-120b"),
             ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "openai/gpt-oss-120b"),
             ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "qwen/qwen3.8-27b"),
             ("https://api.siliconflow.com/v1/chat/completions", "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B"),
             ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b:free")]
    for attempt in range(2):
        for url, envk, model in lanes:
            key = K.get(envk)
            if not key:
                continue
            try:
                r = requests.post(url, timeout=45,
                                  headers={"Authorization": "Bearer " + key,
                                           "Content-Type": "application/json",
                                           "User-Agent": "Apex-Adapter/2.0"},
                                  json={"model": model, "max_tokens": 250,
                                        "temperature": 0.2,
                                        "messages": [{"role": "user", "content": prompt}],
                                        "response_format": {"type": "json_object"}})
                if r.status_code == 200:
                    t = r.json()["choices"][0]["message"]["content"] or ""
                    s = t.find("{")
                    if s != -1 and t.count("{") > t.count("}"):
                        t = t[s:] + "}" * (t.count("{") - t.count("}"))
                    dd = json.loads(t)
                    if isinstance(dd, dict) and dd.get("verdict"):
                        dd["judged_by"] = model
                        return dd
            except Exception:
                pass
        time.sleep(10)
    return {"verdict": "UNJUDGED", "build": "", "reason": "all windows rested"}


pats = collect()
print("[patterns]:", len(pats))
ledger, lines = [], ["# the 10x money-compare", ""]
for name, meta in sorted(pats.items(), key=lambda x: -len(x[1]["passes"])):
    v = judge(name, meta)
    ledger.append({"pattern": name, "passes": meta["passes"], **v})
    print(f"[{v.get('verdict')}] {name} — {str(v.get('reason',''))[:70]}")
os.makedirs(MONEY, exist_ok=True)
with open(os.path.join(MONEY, "improvements.json"), "w", encoding="utf-8") as f:
    json.dump(ledger, f, ensure_ascii=False, indent=1)
with open(os.path.join(MONEY, "compare.md"), "w", encoding="utf-8") as f:
    for l in ledger:
        f.write(f"## {l['pattern']} ({l.get('verdict')})\n{l.get('build','')}"
                f" — {l.get('reason','')}\n\n")
    f.write(f"total judged: {len(ledger)}\n")
now = [l for l in ledger if l.get("verdict") == "IMPROVE-NOW"]
print("[IMPROVE-NOW]:", len(now))
for l in now[:3]:
    print("   build:", l.get("build", "")[:90])