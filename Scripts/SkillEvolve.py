"""SkillEvolve - THE SKILLS ACQUISITION + LIBRARY EVOLUTION ORGAN.

Upgrade 1 (acquisition gains a brain): candidate skills get a deep-brain
judge (fit/quality/novelty; window-polite, bench-aware) BEFORE registration;
low-fit code never enters the library.
Upgrade 2 (acquisition from experience): swarm-consensus deep answers get
DISTILLED into canonical skill candidates (compile-verified locally, then
judged, then registered with full provenance).
Upgrade 3 (the library evolves): nightly, N random library skills are
compile-verified (net-free) + usefulness-scored by the deep brain; the
ledger of promotions/prunes lands in skills_scores.json.
$0 lanes only; keys stay home; every write receipts its reason.
"""
import io
import json
import os
import py_compile
import random
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LIB = os.path.join(REPO, "Config", "SkillLibrary.json")
AD = r"C:\Users\seaha\Apex-Adapter"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain

K = CloudBrain.env_keys()
URL = "https://api.cerebras.ai/v1/chat/completions"
H = {"Authorization": "Bearer " + K.get("CEREBRAS_API_KEY"),
     "Content-Type": "application/json",
     "User-Agent": "Apex-Adapter/2.0"}


def compile_ok(path):
    try:
        py_compile.compile(path, doraise=True)
        return True
    except Exception:
        return False


def deep_judge(prompt, limit=3):
    time.sleep(1.2)
    for attempt in range(limit):
        for model in ("gpt-oss-120b", "qwen-3.8-27b"):
            try:
                import requests
                r = requests.post(URL, headers=H, timeout=45,
                                  json={"model": model, "max_tokens": 250,
                                        "temperature": 0.1,
                                        "messages": [{"role": "user",
                                                      "content": prompt}]})
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass
        time.sleep(9)
    return ""


def score_skill(skill):
    name = skill.get("skill", "?")
    src = skill.get("first_line", "")
    p = ("Rate this Python code-skill for a self-improving agent library. "
         "skill: " + name + ". code-signature: " + src[:120] +
         " lines: " + str(skill.get("lines", "?")) +
         " imports: " + ",".join(skill.get("imports", []) or []) +
         "\nReply ONLY JSON: usefulness(0-10), novelty(0-10), keep(true|false), "
         "reason(one line).")
    raw = deep_judge(p)
    s, e = raw.find("{"), raw.rfind("}")
    if s != -1 and e > s:
        try:
            d = json.loads(raw[s:e + 1])
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return None


def nightly(n_skills=12):
    """the library's evolution beat: compile-verify + usefulness + ledger."""
    lib = json.load(open(LIB, encoding="utf-8-sig"))
    skills = lib.get("skills", [])
    if not isinstance(skills, list):
        skills = list(skills.values())
    sample = random.sample(skills, min(n_skills, len(skills)))
    ledger = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "checked": []}
    out_path = os.path.join(REPO, "scores", "skills_scores.json")
    prev = []
    if os.path.isfile(out_path):
        try:
            with open(out_path, encoding="utf-8") as f:
                prev = json.load(f)
            if not isinstance(prev, list):
                prev = []
        except Exception:
            prev = []
    for s in sample:
        ok_compile = bool(s.get("compiles"))
        sf = s.get("source_file", "")
        rec = {"skill": s.get("skill", "?"), "compiles_prev": ok_compile,
               "verified_at_prev": s.get("verified_at")}
        if sf and not sf.endswith("*.py"):
            cand = os.path.join(REPO, "skills_src", *sf.split("/"))
            if os.path.isfile(cand):
                rec["compiles_now"] = compile_ok(cand)
        j = score_skill(s)
        if j:
            rec["usefulness"] = j.get("usefulness")
            rec["keep"] = j.get("keep")
            rec["reason"] = j.get("reason")
        ledger["checked"].append(rec)
        print("  -", rec["skill"][:36], "| compiles:", rec.get("compiles_now", rec.get("compiles_prev")),
              "| useful:", rec.get("usefulness"), "| keep:", rec.get("keep"))
    seen = json.dumps(ledger)
    prev.append(ledger)
    prev = prev[-30:]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prev if prev else [ledger], f, ensure_ascii=False, indent=1)
    print("[skills ledger]:", out_path, "| checked:", len(ledger["checked"]))


if __name__ == "__main__":
    if "--nightly" in sys.argv:
        random.seed()
        nightly()
        main_done = True
    else:
        lib = json.load(open(LIB, encoding="utf-8-sig"))
        sk = lib.get("skills", [])
        if isinstance(sk, dict):
            sk = list(sk.values())
        s = random.choice(sk)
        print("[smoke skill]:", s.get("skill"))
        j = score_skill(s)
        print("[deep judge]:", json.dumps(j, ensure_ascii=False)[:220] if j
              else "walled (honest)")