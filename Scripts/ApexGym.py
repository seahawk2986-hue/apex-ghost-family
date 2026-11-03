"""ApexGym v2 - THE GENERAL-INTELLIGENCE TRAINING ORGAN (outsourced).

Novel core: EVERY drill carries its own truth-checker. GI families:
  arithmetic-chain  - multi-step precise math; truth = local python eval of
                      the drill's verify_py (objective, $0)
  math-word         - word problems reducible to an expression; same check
  predict-output    - short snippet; truth = local exec (objective)
  spot-the-flaw     - the generator embeds a flaw + its canonical name;
                      grading = keyword containment (objective)
Teachers (drill GEN + lesson REFLECTION) = REMOTE fleet brains (outsourced);
truth = the one local micro-exec (brain-bound light). Misses -> council
lessons -> the episodic ledger (the exact family format) -> committed for
the off-box distillation. 28-min cap; window-polite; $0 forever.
"""
import io
import json
import os
import random
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(REPO, "apex_venv", "Scripts", "python.exe")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain

K = CloudBrain.env_keys()
def _flag_int(name, default):
    if name in sys.argv:
        try:
            return max(1, int(sys.argv[sys.argv.index(name) + 1]))
        except (ValueError, IndexError):
            return default
    return default


# (the 2026-11-04 fix: callers have passed --minutes/--traits for the machine's
# whole life while only --smoke was parsed - the flag-drift class bug that made
# every scheduled gym die inside its own subprocess timeout as "GYM skipped".
# Flags are parsed now; --traits X is accepted and honored as a note.)
GYM_MINUTES = _flag_int("--minutes", 8 if "--smoke" in sys.argv else 28)
_traits = "auto"
if "--traits" in sys.argv:
    try:
        _traits = sys.argv[sys.argv.index("--traits") + 1]
    except IndexError:
        _traits = "auto"
WALL_END = time.time() + 60 * GYM_MINUTES
TEACHERS = [  # top-tier first; the leaderboard re-ranks them nightly
    ("cerebras", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "gpt-oss-120b"),
    ("groq", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b"),
    ("groq-qwen", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "qwen/qwen3.8-27b"),
    ("sflow", "https://api.siliconflow.com/v1/chat/completions",
     "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B"),
    ("or-ultra", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("cerebras-q", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "qwen-3.8-27b"),
]
FAMILIES = ["self-forecast", "self-forecast", "arithmetic-chain",
            "arithmetic-chain", "predict-output", "spot-the-flaw",
            "math-word", "self-forecast"]     # GI-weighted, metacognition-heavy

GEN = {
 "self-forecast": "Reply ONLY JSON: {\"question\": one short factual/reasoning Q; "
   "the trainee must answer AND predict their own correctness (high/med/low) in "
   "the form 'answer | confidence: high|medium|low', \"answer\": the exact short "
   "correct answer, \"verify_py\": python expression equal to that answer}. No fences.",
 "arithmetic-chain": "Generate ONE multi-step arithmetic-chain drill (3-4 steps: e.g. "
   "percentages, ratios, unit conversions). Reply ONLY JSON: {\"question\": the "
   "worded multi-step problem, \"verify_py\": a python expression evaluating to "
   "the exact answer}. No code fences.",
 "math-word": "Generate ONE short math word problem solvable by a single "
   "expression. Reply ONLY JSON: {\"question\": ...one sentence problem..., "
   "\"verify_py\": expression giving the exact numeric answer}. No fences.",
 "predict-output": "Reply ONLY JSON: {\"question\": 'What does this print?' , "
   "\"code\": a <=10-line python snippet printing exactly one line, "
   "\"verify_py\": the exact stdout line as a quoted string}. No fences.",
 "spot-the-flaw": "Reply ONLY JSON: {\"question\": one sentence containing a "
   "clear reasoning flaw for the trainee to name, \"flaw\": the flaw's canonical "
   "name (2-3 words), \"verify_py\": 'ok'}. No fences.",
}


GEN_LANES = TEACHERS[:2]      # drill-farming = the FAST top lanes (volume)
REFLECT_LANES = TEACHERS      # the reflection/judgment = the full top-tier


def teacher(prompt, lanes=None):
    # THE SPINE-FIRST (2026-11-04): the organ's prompts route through the
    # family's ONE dispatch (pacing honored, rotator receipt, all our models
    # get real traffic from every organ beat); the private TEACHERS array
    # stays as the fallback when the spine import fails.
    try:
        import ApexShard as _Shard
        _nm, _md, _txt, _notes = _Shard.call(
            _Shard.env(), _Shard.order_for(tier3=False),
            [{"role": "user", "content": prompt}], max_tokens=600)
        if _txt and _txt.strip():
            time.sleep(1.5)
            return _txt.strip(), f"{_nm}"
    except Exception:
        pass
    import requests
    for name, url, envk, model in (lanes or TEACHERS):
        key = K.get(envk)
        if not key:
            continue
        try:
            r = requests.post(url, timeout=45,
                              headers={"Authorization": "Bearer " + key,
                                       "Content-Type": "application/json",
                                       "User-Agent": "Apex-Adapter/2.0"},
                              json={"model": model, "max_tokens": 600,
                                    "temperature": 0.5,
                                    "messages": [{"role": "user", "content": prompt}]})
            if r.status_code == 200:
                t = (r.json()["choices"][0]["message"]["content"] or "").strip()
                time.sleep(1.5)
                return t, f"{name}/{model.split('/')[-1]}"
        except Exception:
            continue
    return "", None


def gen_drill(kind):
    d, src = teacher(GEN[kind])
    if not d:
        return None, None, None
    s = d.find("{")
    if s != -1 and d.count("{") > d.count("}"):
        d = d[s:] + "}" * (d.count("{") - d.count("}"))
    try:
        j = json.loads(d)
        return j, j.get("verify_py"), src
    except Exception:
        return None, None, src


def truth(j):
    vp = j.get("verify_py", "")
    if j.get("code"):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         dir=os.environ.get("TEMP", ".")) as f:
            f.write(j["code"])
            p = f.name
        try:
            r = subprocess.run([PY, "-I", p], capture_output=True,
                               text=True, timeout=15)
            return r.stdout.strip()[:300]
        finally:
            try:
                os.remove(p)
            except Exception:
                pass
    if vp and vp != "ok":
        try:
            v = eval(vp, {"__builtins__": {}}, {})
            return v if isinstance(v, str) else repr(v)   # no quote-artifacts
        except Exception:
            return None
    return vp or None


def grade(j, forecast):
    f = (forecast or "").strip()
    conf = None
    if "| confidence:" in f.lower():
        try:
            ans, conf = f.split("| confidence:", 1)
            f = ans.strip()
            conf = conf.strip().split()[0].lower()
        except Exception:
            conf = None
    if j.get("code"):
        return f == (j.get("verify_py") or "").strip(), conf
    flaw = j.get("flaw", "")
    if flaw:
        return (flaw.lower() in f.lower() or
                flaw.lower().replace("-", " ") in f.lower()), conf
    want = str(j.get("verify_py", ""))
    try:
        lhs = eval(want, {"__builtins__": {}}, {})   # the expression's VALUE counts
        if isinstance(lhs, str):
            # the 11/02 fix: quoted string truths graded by VALUE, not by quote-artifact
            lf = f.lower()
            ll = lhs.lower()
            return (lf == ll or (ll != "" and ll in lf)), conf
        return abs(float(lhs) - float(f)) < 1e-9, conf
    except (ValueError, TypeError, SyntaxError):
        pass
    return want in f.replace(" ", ""), conf


def remember(kind, text, meta, imp=0.6):
    uid = os.urandom(6).hex()
    rec = {"id": uid, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": kind, "text": text, "meta": meta, "imp": imp}
    with open(EPISODIC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    n_hit = n_done = 0
    print(f"[gym]: the GI organ armed — minutes={GYM_MINUTES}, traits={_traits}, "
          f"smoke={'yes' if '--smoke' in sys.argv else 'no'}")
    lessons = []          # the curriculum: tonight's own lessons re-teach
    fams = FAMILIES * (1 if "--smoke" in sys.argv else 3)
    random.shuffle(fams)
    for i, kind in enumerate(fams):
        if time.time() > WALL_END:
            break
        j, vp, src = gen_drill(kind)
        if not j or not j.get("question"):
            remember("gym_miss", "drill gen walled", {"family": kind})
            time.sleep(15)
            continue
        out = truth(j)
        q = j["question"][:160]
        teach = ""
        if lessons:
            teach = ("\n[THE TRAINEE'S OWN LESSONS SO FAR - apply them]:\n"
                     + "\n".join("- " + l for l in lessons[-3:]))
        forecast, lane = teacher(
            "Answer with ONLY the required answer: the exact output/number/"
            "flaw-name. If the prompt asks for confidence, keep it. No "
            "explanation.\n" + q + teach)
        hit, conf = grade(j, forecast)
        n_hit += hit
        n_done += 1
        meta = {"family": kind, "hit": hit}
        if conf:
            meta["claimed"] = conf
            remember("metacognition",
                     f"self-forecast: claimed {conf}, got "
                     f"{'HIT' if hit else 'MISS'}"
                     + (" <- OVERCONFIDENT (the calibration violation)"
                        if conf == "high" and not hit else ""),
                     meta, imp=0.7)
        remember("calibration",
                 (f"GI gym[{kind}] HIT (teacher={lane})" if hit else
                  f"GI gym[{kind}] MISS (teacher={lane}, truth={str(out)[:50]!r})"),
                 meta)
        print(f"[{kind}] {q[:56]} -> {str(forecast)[:48]!r} "
              f"{'HIT' if hit else 'MISS (truth ' + str(out)[:28] + ')'}")
        if not hit:
            lesson, _ = teacher(
                f"Training miss. Problem: {q} | correct: {str(out)[:80]!r} | "
                "write ONE durable lesson (<=35 words) on the general principle.")
            if lesson:
                lessons.append(lesson.strip()[:160])
                remember("lesson", lesson[:220],
                         {"teacher": lane, "family": kind}, imp=0.8)
                print("   lesson:", lesson[:78])
        time.sleep(2)
    remember("gym_pass", f"GI-gym beat: {n_done} drills, {n_hit} hits "
             "(outsourced teachers)", {})
    print(f"[GI beat]: {n_done} drills | {n_hit} hits")
    for cmd in (["git", "add", "memory_episodic.jsonl"],
                ["git", "commit", "-m", "episodic: the GI-gym feed for the off-box distill [skip ci]"]):
        subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


random.seed()

# THE __main__ GUARD (2026-11-04): the gym used to RUN ITSELF when merely
# imported (module-level main()) - now import == safe; running == explicit.
if __name__ == "__main__":
    main()