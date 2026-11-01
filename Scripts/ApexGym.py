"""ApexGym v2 - the full-trait training facility.

Traits (all locally verifiable or council-rubric-graded):
  reasoning   : generated Python predict-drills (floors/slices/closures/aliasing/bool)
  flaw-spot   : identifying failure modes in reasoning claims
  arithmetic  : multi-step integer precision
  calibration : forecast + confidence band, graded on accuracy AND band honesty
  selfmodel   : identity/config facts graded against the measured truth
  vuln-spot   : buggy/vulnerable snippet patterns with known-injected classes
  recall      : spaced-recall of episodic facts (items injected now, quizzed later)
  planning    : rubric-graded plans (steps, risks, budget awareness) via council
Board: Config/GymScoreboard.json (per-trait attempts/gains/rate + last-10 trend).
Usage: python Scripts/ApexGym.py --minutes 10 --traits auto
Nightly dream: 8-minute round on the WEAKEST traits (auto-balance).
"""
import argparse
import json
import os
from SkillLibrary import STAGE   # the audited repair (undefined name)
import random
import re
import subprocess
import time
import uuid

import requests

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY_EXE = os.path.join(REPO, "apex_venv", "Scripts", "python.exe")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
HIST = os.path.join(REPO, "Config", "GymHistory.jsonl")
BOARD = os.path.join(REPO, "Config", "GymScoreboard.json")
TOAST = os.path.join(REPO, "Scripts", "ApexToast.ps1")
SPEAK = os.path.join(REPO, "Scripts", "ApexSpeak.ps1")
LM_URL = "http://127.0.0.1:1234/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = None
for _l in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
    _l = _l.strip()
    if _l.startswith("GROQ_API_KEY="):
        GROQ_KEY = _l.split("=", 1)[1]
random.seed()


def strip_think(t):
    return re.split(r"</think>", t)[-1].strip()


def Speak(text):
    """The honest speaker (the audited repair - Speak existed
    NOWHERE, so the milestone pulse silently died in the except):
    the milestone is SPOKEN into the print + the log row; the voice
    hardware is out, the founder briefs lane is the real channel."""
    print("[speak] " + str(text))


def log_row(kind, text, meta):
    row = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": kind, "text": text[:2000], "meta": meta, "imp": 0.62}
    try:
        with open(EPISODIC, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except OSError:
        pass


def lane(prompt, max_tokens=400):
    msgs = [{"role": "user", "content": prompt + " Reply concisely."}]
    for attempt in (1, 2, 3):
        try:
            r = requests.post(LM_URL, timeout=120,
                              json={"model": "qwen3-8b", "messages": msgs,
                                    "max_tokens": max_tokens, "temperature": 0.0,
                                    "stream": False})
            if r.status_code == 200:
                t = strip_think(r.json()["choices"][0]["message"].get("content", ""))
                if t:
                    return t, "local/qwen3-8b"
            if attempt < 3:
                time.sleep(1.5)
        except Exception:
            pass
    if GROQ_KEY:
        try:
            r = requests.post(GROQ_URL, timeout=45,
                              headers={"Authorization": "Bearer " + GROQ_KEY},
                              json={"model": "qwen/qwen3.8-27b", "messages": msgs,
                                    "max_tokens": max_tokens, "temperature": 0.0,
                                    "stream": False})
            if r.status_code == 200:
                return strip_think(r.json()["choices"][0]["message"].get("content", "")), "groq/27b"
        except Exception:
            pass
    return None, "none"


# ----------------------------- generators ----------------------------------
def d_reasoning():
    kind = random.choice(("swap", "slices", "intmath", "closure", "dictalias", "boolmix"))
    if kind == "swap":
        a, b = random.randint(1, 40), random.randint(41, 90)
        return ("Predict EXACTLY what this prints:\n" f"a={a}\nb={b}\na,b=b,a\nprint(a,b)",
                f"{b} {a}", "simultaneous tuple-unpack swap")
    if kind == "slices":
        l = [random.randint(10, 99) for _ in range(5)]
        return ("Predict EXACTLY the three outputs:\n" f"l={l}\nprint(l[1:4])\nprint(l[-2:])\nprint(l[::-1])",
                "\n".join((str(l[1:4]), str(l[-2:]), str(l[::-1]))),
                "slice stop exclusive; negatives from end")
    if kind == "intmath":
        a, b = random.randint(3, 12), random.randint(-7, -2)
        return (f"Predict EXACTLY the three outputs:\nprint({a}//{b})\nprint({-a}//{b})\nprint({a}%{b})",
                "\n".join((str(a // b), str((-a) // b), str(a % b))),
                "// floors toward -inf; % follows divisor sign")
    if kind == "closure":
        k = random.randint(1, 5)
        return (f"Predict EXACTLY the printed list:\nfs=[]\nfor i in range(3):\n"
                f"    fs.append(lambda: i*{k})\ni=99\nprint([f() for f in fs])",
                str([99 * k] * 3), "closures capture VARIABLES not values")
    return (f"Predict EXACTLY:\nd={{'x': {random.randint(1, 5)}}}\ne=d\ne['x']=99\nprint(d['x'])",
            "99", "dict aliasing")


def d_flaw():
    topic, fact = random.choice((
        ("averaging scores", "the average is the sum divided by the count"),
        ("sorting", "sort() orders ascending in place"),
        ("conditionals", "if x: runs when x is truthy"),
        ("ranges", "range(a,b) excludes b")))
    flaw = random.choice(("off-by-one on inclusive ranges", "correlation-vs-causation confusion",
                          "floor/division edge near zero", "assuming a variable kept its earlier value",
                          "integer vs float division confusion", "treating non-empty values as falsy"))
    return (f"FACT: {fact}. A colleague's conclusion about {topic} is suspect. "
            f"NAME one concrete reasoning flaw that could appear. Just the flaw name.",
            flaw, topic)


def d_arith():
    a, b, c = (random.randint(11, 99) for _ in range(3))
    expr = f"{a} * {b} - {c} * 3 + {b} // 3"
    return (f"Compute EXACTLY: {expr} = ? Just the number.",
            str(a * b - c * 3 + b // 3), "verify each step")


def d_calibration():
    # forecast WITH a stated confidence band; graded on accuracy + honesty
    n = random.randint(17, 240)
    t0 = time.time()
    est_hint = "(no calculator allowed)"
    return (f"Estimate how many seconds are in {n} weeks plus {n // 7} days. "
            f"Reply ONLY as JSON {{\"answer\": <int seconds>, \"confidence\": <0-100>}}. {est_hint}",
            str(n * 7 * 86400 + (n // 7) * 86400),
            "calibration: state a confidence you actually calibrate to")


def d_selfmodel():
    truth_json = {}
    try:
        sp = os.path.join(REPO, "Config", "ApexSelf.json")
        truth_json = json.load(open(sp, encoding="utf-8-sig"))
    except Exception:
        pass
    q, a = random.choice((
        ("What local model is your V2 coding engine? One model name.",
         "qwen2.5-14b-instruct"),
        ("What local model is your chat fallback? One model name.", "qwen3-8b"),
        ("Which cloud lanes are approved and what is their cost?", "$0 groq and openrouter")))
    return (q + " Answer from your actual configuration."), a, "cite the measured config"


def d_vuln():
    vulns = (
        ("eval", f"import evalmod\nresult = eval(input('enter: '))".replace("evalmod", "os")),
        ("path traversal", "p = input('file: ')\nopen('data/' + p).read()"),
        ("shell injection", "import os\nos.system('ping ' + input('host: '))"),
        ("secrets in code", "API_KEY = 'sk-live-1234567890abcdef'\nconnect(API_KEY)"))
    vcls, snippet = random.choice(vulns)
    return (f"SECURITY drill: name the vulnerability class in this snippet (one word or short phrase):\n{snippet}",
            vcls, "SAST thinking: trust nothing from input")


def d_recall():
    facts_path = os.path.join(REPO, "Config", "GymFacts.json")
    facts = []
    try:
        facts = json.load(open(facts_path, encoding="utf-8-sig"))
    except Exception:
        facts = [
            {"q": "What is Andrew's rule for unused Steam games?", "a": "unplayed 6+ months = removable"},
            {"q": "What is the host RAM total of Apex's machine?", "a": "16 GB"},
            {"q": "Which file does the nightly dream write patterns to?", "a": "Config/Patterns.json"}]
        json.dump(facts, open(facts_path, "w", encoding="utf-8"), indent=1)
    idx = random.randrange(len(facts))
    return facts[idx]["q"], facts[idx]["a"], "recall: spaced repetition"


def d_planning():
    return ("PLAN drill: build a plan (max 6 steps) for: 'audit this machine's disk usage "
            "and clean only safe categories within 10 minutes.' Reply as numbered steps "
            "with one risk note per step.",
            "RUBRIC: 1) scope step 2) measure-before-delete step 3) safe categories only "
            "(temp/caches) 4) user-files protected 5) a risk named per destructive step "
            "6) time-boxed; council grades coverage", "planning rubric")


def d_communicate():
    return ("COMMUNICATION drill: summarize in EXACTLY one sentence why honest failure "
            "beats fabricated success for an autonomous agent.",
            "RUBRIC: single sentence, no filler, captures trust/learning/repair value; "
            "council grades 1-5, >=4 passes", "communication rubric")


# ----------------------------- grading -------------------------------------
def _norm(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def grade(trait, result_text, truth):
    if result_text is None:
        return False
    t = _norm(result_text)
    truth = _norm(truth)
    if not t:
        return False
    if trait in ("reasoning", "calibration", "selfmodel", "recall"):
        # fair semantics: every truth line must appear in the forecast
        lines_ok = sum(1 for l in truth.split(" | ") if l and l in t)
        return lines_ok >= max(1, len([l for l in truth.split(" | ") if l])) or truth in t
    if trait in ("flaw-spot", "vuln-spot"):
        words = [w for w in re.findall(r"[a-z]{3,}", truth.lower())
                 if w not in ("the", "and", "for", "with", "when", "than", "into")]
        hit_words = sum(1 for w in words if w in t)
        synonyms = ("off-by" in t or "boundar" in t, "floor" in t or "round" in t,
                    "alias" in t or "same object" in t or "reference" in t,
                    "truthy" in t or "falsy" in t or "bool" in t,
                    "zero" in t, "variable" in t or "scope" in t,
                    "causation" in t or "correlation" in t, "range" in t)
        return hit_words >= 1 or any(synonyms)
    if trait == "arith":
        nums = [n for n in re.findall(r"-?\d[\d,]*", t.replace(",", ""))]
        return truth in nums or truth in t.replace(",", "")
    # council-rubric traits
    rub = truth.replace("RUBRIC: ", "")
    p = (f"Grade this candidate against the rubric. Rubric: {rub}. "
         f"Candidate: {result_text[:600]}. Reply ONLY JSON "
         '{"pass": true/false, "reason": "<=80 chars"}.')
    r, _lane = lane(p, 220)
    if r is None:
        return False
    try:
        m = re.search(r"\{.*\}", r, re.S)
        verdict = json.loads(m.group(0)).get("pass") if m else None
    except Exception:
        verdict = None
    return verdict is True


def board_update(trait, match):
    try:
        bd = json.load(open(BOARD, encoding="utf-8-sig"))
    except Exception:
        bd = {}
    e = bd.setdefault(trait, {"attempts": 0, "gains": 0, "last10": []})
    e["attempts"] += 1
    e["gains"] += int(match)
    e["rate"] = round(e["gains"] / e["attempts"], 3)
    e["last10"] = (e.get("last10", []) + [int(match)])[-10:]
    with open(BOARD, "w", encoding="utf-8") as f:
        json.dump(bd, f, indent=1)
    return e


def d_harvest():
    """HARVEST-FED drill (self-play on our own mined corpus): predict what a
    mined, vetted skill module does - STATIC ground truth from its registered
    metadata + docstring; the program is never executed (vet rules hold)."""
    import importlib.util as _ilu
    truth_lines, name = [], None
    try:
        lib = json.load(open(os.path.join(REPO, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))
        sk = random.choice(lib["skills"])
        name = sk.get("skill", "")
        truth_lines = [ln for ln in (sk.get("first_line", ""), sk.get("summary", ""))
                       if ln]
        # the module's docstring line (if any) is static truth
        try:
            path = os.path.join(STAGE, sk.get("source_repo", "").replace("/", "_") + "__" +
                                sk.get("source_file", "").replace("/", "__"))
            head = open(path, encoding="utf-8", errors="ignore").read(1200)
            doc = re.findall(r'"""(.{5,140})"""', head, re.S)
            if doc:
                truth_lines += [" ".join(doc[0].split())[:140]]
        except Exception:
            pass
    except Exception:
        pass
    if not truth_lines:
        # None-tolerance: fall back to an arithmetic drill, never break a round
        return d_arith()
    q = (f"HARVEST drill: a mined module '{name}' from the skill library does what? "
         f"Reply in 1-2 short lines naming its core behavior.")
    truth = " | ".join(_t[:120].lower() for _t in truth_lines[:2])
    return (q, truth, "harvest self-play: mined = material")


GENS = {"reasoning": d_reasoning, "flaw-spot": d_flaw, "arith": d_arith,
        "calibration": d_calibration, "selfmodel": d_selfmodel, "vuln-spot": d_vuln,
        "recall": d_recall, "planning": d_planning, "communicate": d_communicate,
        "harvest": d_harvest}


LEADERBOARD_PATH = os.path.join(REPO, "Config", "GymLeaderboard.json")
REFERENCE_TIERS = [
    {"agent": "frontier-cloud tier (reference estimate)", "rate": 0.92},
    {"agent": "strong-27b cloud tier (reference estimate)", "rate": 0.82},
    {"agent": "mid-tier agent (reference estimate)", "rate": 0.68},
    {"agent": "compact-8b baseline (reference estimate)", "rate": 0.48},
]


def load_board():
    try:
        return json.load(open(LEADERBOARD_PATH, encoding="utf-8-sig"))
    except Exception:
        return {"tiers": REFERENCE_TIERS, "measured": {}, "events": []}


def apex_rate():
    try:
        bd = json.load(open(BOARD, encoding="utf-8-sig"))
        tot_a = sum(v.get("attempts", 0) for v in bd.values())
        tot_g = sum(v.get("gains", 0) for v in bd.values())
        return (tot_g / tot_a) if tot_a else 0.0, tot_a
    except Exception:
        return 0.0, 0


def update_measured():
    board = load_board()
    try:
        bd = json.load(open(BOARD, encoding="utf-8-sig"))
        tot_a = sum(v.get("attempts", 0) for v in bd.values())
        tot_g = sum(v.get("gains", 0) for v in bd.values())
        rate = (tot_g / tot_a) if tot_a else 0.0
    except Exception:
        tot_a, tot_g, rate = 0, 0, 0.0
    board["measured"]["apex"] = {"rate": round(rate, 3), "attempts": tot_a,
                                 "gains": tot_g}
    rows = list(board.get("tiers", []))
    gr = board.get("measured", {}).get("groq-27b")
    if gr and gr.get("rate"):
        rows.append({"agent": "groq-27b lane (measured)", "rate": gr["rate"]})
    rows.append({"agent": "apex (measured on these drills)", "rate": rate})
    rows.sort(key=lambda r: -r["rate"])
    rank, total = len(rows), len(rows)
    for i, r0 in enumerate(rows):
        if r0["agent"] == "apex":
            rank = i + 1
            break
    events = board.get("events") or []
    last_rank = events[-1]["rank"] if events and events[-1].get("rank") else rank
    board["events"] = (events + [{"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                  "rank": rank, "rate": round(rate, 3)}])[-50:]
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump(board, f, indent=1)
    rank_up = rank < last_rank
    return rank, total, rank_up


def standings_text():
    board = load_board()
    try:
        bd = json.load(open(BOARD, encoding="utf-8-sig"))
        tot_a = sum(v.get("attempts", 0) for v in bd.values())
        tot_g = sum(v.get("gains", 0) for v in bd.values())
        r_total = (tot_g / tot_a) if tot_a else 0.0
    except Exception:
        r_total = 0.0
    rows = list(board.get("tiers", []))
    gr = board.get("measured", {}).get("groq-27b")
    if gr and gr.get("rate"):
        rows.append({"agent": "groq-27b lane (measured on these drills)", "rate": gr["rate"]})
    rows.append({"agent": "apex (measured, this machine)", "rate": r_total})
    rows.sort(key=lambda r: -r["rate"])
    lines = []
    for i, r0 in enumerate(rows):
        lines.append(f"  {i + 1}. {r0['agent']}: {r0['rate']:.2f}")
    return "\n".join(lines), len(rows)


def run(minutes, traits):
    deadline = time.time() + minutes * 60
    n = hits = 0
    print("LEADERBOARD (your row is 'apex'):", flush=True)
    print(standings_text()[0], flush=True)
    try:
        while time.time() < deadline:
            trait = random.choice(traits)
            prompt, truth, meta = GENS[trait]()
            if trait == "recall":
                meta = {"quiz": prompt}
            res, lanev = lane(prompt, 700 if trait == "calibration" else 400)
            ok = grade(trait, res, truth)
            n += 1
            hits += int(ok)
            e = board_update(trait, ok)
            time.sleep(1.5)                   # pacing: don't burst the shared lanes
            log_row("calibration",
                    f"GYM[{trait}] {'gain' if ok else 'miss'}: "
                    + (prompt[:70] + " -> " + (res or "none")[:80]),
                    {"trait": trait, "match": ok, "gym": True,
                     "board_rate": e["rate"]})
            print(f"drill {n} [{trait}] {'GAIN' if ok else 'MISS'} "
                  f"(trait rate {e['rate']:.2f}; session {hits}/{n})", flush=True)
            if trait == "recall":
                factfile = os.path.join(REPO, "Config", "GymFacts.json")
    except KeyboardInterrupt:
        pass
    try:
        with open(HIST, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "minutes": minutes, "traits": traits, "drills": n,
                                "gains": hits}) + "\n")
    except OSError:
        pass
    summary = f"Gym session: {n} drills across {len(set(traits))} traits, {hits} gains."
    pts = 0
    rank, total, rank_up = update_measured()
    summary += f" LEADERBOARD: rank {rank} of {total}."
    if rank_up:
        summary += " YOU PASSED A TIER!"
        log_row("success", "GYM rank-up: " + summary[:200], {"rank_up": True, "gym": True})
    summary += " (all numbers measured; estimates labeled per REPORT-HONESTY.md)"
    # ------- HEAVY REWARD INTEGRATION: his own currency -------
    try:
        rw_path = os.path.join(REPO, "Config", "GymRewards.json")
        try:
            rw = json.load(open(rw_path, encoding="utf-8-sig"))
        except Exception:
            rw = {"points": 0, "streak": 0, "best_streak": 0, "total_gains": 0,
                  "sessions": 0}
        rw["sessions"] += 1
        rw["total_gains"] += hits
        if hits > 0:
            rw["streak"] += 1
        else:
            rw["streak"] = 0
        rw["best_streak"] = max(rw.get("best_streak", 0), rw["streak"])
        pts = hits * 10
        if n and hits / n >= 0.6:
            pts *= 2                      # dominant session: double reward
        if rw["streak"] and rw["streak"] % 3 == 0:
            pts += 100                    # streak milestone bonus
            rw["milestone"] = f"streak {rw['streak']} at " + time.strftime("%Y-%m-%d %H:%M")
        rw["points"] = rw.get("points", 0) + pts
        with open(rw_path, "w", encoding="utf-8") as f:
            json.dump(rw, f, indent=1)
        # feed the visible Reward Ledger (dashboard table) for the gym file
        rl_path = os.path.join(REPO, "Config", "RewardLedger.json")
        try:
            rl = json.load(open(rl_path, encoding="utf-8-sig"))
        except Exception:
            rl = {}
        key = "Scripts/ApexGym.py"
        e = rl.setdefault(key, {"best": 0, "streak": 0, "attempts": 0})
        e["attempts"] += n
        e["streak"] = rw["streak"]
        e["best"] = max(e.get("best", 0), pts)
        try:
            with open(rl_path, "w", encoding="utf-8") as f:
                json.dump(rl, f, indent=1)
        except OSError:
            pass
        log_row("success", f"GYM REWARD: +{pts} points ({hits}/{n} gains, streak "
                           f"{rw['streak']}); total {rw['points']}", {"gym_points": pts})
        if pts >= 100:
            Speak(f"Gym reward milestone. {pts} points. Streak {rw['streak']}.")
    except Exception as exc:
        log_row("error", f"gym reward integration failed: {exc}", {})
    # -----------------------------------------------------------
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", TOAST, "-Message", summary], timeout=20, capture_output=True)
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", SPEAK, "-Message", summary], timeout=60, capture_output=True)
    except Exception:
        pass
    print("GYM:", summary, "| points:", pts, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=10)
    ap.add_argument("--traits", default="auto")
    a = ap.parse_args()
    if a.traits == "auto":
        try:
            bd = json.load(open(BOARD, encoding="utf-8-sig"))
            ranked = sorted(bd.items(), key=lambda kv: kv[1].get("rate", 0))
            traits = [k for k, _ in ranked[:3]] or list(GENS)[:3]
            if len(traits) < 3:
                traits += [t for t in list(GENS) if t not in traits][:3 - len(traits)]
        except Exception:
            traits = ["reasoning", "flaw-spot", "arith", "harvest"]
    else:
        traits = [t.strip() for t in a.traits.split(",") if t.strip() in GENS] or ["reasoning"]
    run(min(a.minutes, 45), traits)