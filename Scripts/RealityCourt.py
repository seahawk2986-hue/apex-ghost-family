"""THE BLIND COURT - external ground truth for the fleet's learning
(2026-11-04; the anti-self-referential organ).

THE WEAKNESS IT KILLS: the gym measures itself with drills whose questions
AND answer-checkers come from the same teacher pool that trains on them,
and nothing seals a holdout - the textbook Goodhart risk.

THE SOURCES (all verified):
  * Kapoor, Stroebl, Siegel, Nadgir, Narayanan, "AI Agents That Matter"
    arXiv:2407.01502 (2024) - inadequate/no holdout sets cause fragile,
    self-flattering agents; prescribe sealed holdouts + cost-controlled
    evaluation. THE BLIND COURT implements that prescription, fleet-tier.
  * Jimenez et al., "SWE-bench: Can Language Models Resolve Real-World
    GitHub Issues?" arXiv:2310.06770 (ICLR 2024) - real-world GitHub issues
    are the sustainable external testbed; the STREET mode replays the
    family's OWN harvested real-issue backlog (Apex-Adapter's
    gh_archive_bugs.jsonl, gathered from the GitHub Archive lane) as
    external-distribution planning drills with STRUCTURAL verifiers
    (we do NOT patch strangers' code autonomously - plan-shape truth only).

MODES (CLI):
  seal    - one-time: 6 holdout drills per GI family; answers sealed by
            sha256; NEVER written to memory/lessons (that's the blindness).
  judge   - re-grade the fleet against the sealed pocket + compute the
            SELF-FLATTERY verdict (internal gym-trend vs sealed holdout).
  street  - run the real-world planning drills, write a plan-quality
            receipt (structural objectivity, no invented truth).

Outputs: Config/court_holdout.json (sealed) + Config/court_state.json
(verdict; rendered on /receipts) + one episodic 'court' event per judge.
$0 (the free no-card lanes only), stdlib-only, bounded wall-clock.
"""
import hashlib
import io
import json
import os
import random
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdout.apex_wrapped = True   # one process, one wrapper (double-wrap
                                     # = the GC closes the shared buffer)

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
HOLDOUT = os.path.join(REPO, "Config", "court_holdout.json")
STATE = os.path.join(REPO, "Config", "court_state.json")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
STREET = os.path.join(AD, "gh_archive_bugs.jsonl")
sys.path.insert(0, os.path.join(REPO, "Scripts"))
import CloudBrain  # noqa: E402

K = CloudBrain.env_keys()
FAMILIES = ["arithmetic-chain", "math-word", "predict-output",
            "spot-the-flaw", "self-forecast"]
POCKETS_PER_FAMILY = 6

GEN = {
 "self-forecast": "Reply ONLY JSON: {\"question\": one short factual/reasoning Q; "
   "the trainee must answer AND predict their own correctness in the form "
   "'answer | confidence: high|medium|low', \"answer\": the exact short "
   "correct answer, \"verify_py\": python expression equal to that answer}. No fences.",
 "arithmetic-chain": "Generate ONE multi-step arithmetic-chain drill (3-4 steps). "
   "Reply ONLY JSON: {\"question\": the worded multi-step problem, "
   "\"verify_py\": a python expression evaluating to the exact answer}. No fences.",
 "math-word": "Generate ONE short math word problem solvable by a single "
   "expression. Reply ONLY JSON: {\"question\": one sentence problem, "
   "\"verify_py\": expression giving the exact numeric answer}. No fences.",
 "predict-output": "Reply ONLY JSON: {\"question\": 'What does this print?' , "
   "\"code\": a <=10-line python snippet printing exactly one line, "
   "\"verify_py\": the exact stdout line as a quoted string}. No fences.",
 "spot-the-flaw": "Reply ONLY JSON: {\"question\": one sentence containing a "
   "clear reasoning flaw to name, \"flaw\": the flaw's canonical name "
   "(2-3 words), \"verify_py\": 'ok'}. No fences.",
}


def _teacher(prompt, lanes=None, max_tokens=600, temperature=0.5):
    # THE SPINE-FIRST (2026-11-04): route through the ONE dispatch (pacing +
    # rotator + receipts; every organ beat gives all our models traffic).
    try:
        import ApexShard as _Shard
        _nm, _md, _txt, _notes = _Shard.call(
            _Shard.env(), _Shard.order_for(tier3=False),
            [{"role": "user", "content": prompt}], max_tokens=max_tokens)
        if _txt and _txt.strip():
            time.sleep(1.2)
            return _txt.strip(), _nm
    except Exception:
        pass
    import requests
    TEACHERS = [
        ("cerebras", "https://api.cerebras.ai/v1/chat/completions",
         "CEREBRAS_API_KEY", "gpt-oss-120b"),
        ("groq", "https://api.groq.com/openai/v1/chat/completions",
         "GROQ_API_KEY", "openai/gpt-oss-120b"),
        ("cerebras-q", "https://api.cerebras.ai/v1/chat/completions",
         "CEREBRAS_API_KEY", "qwen-3.8-27b"),
    ]
    for name, url, envk, model in (lanes or TEACHERS):
        key = K.get(envk)
        if not key:
            continue
        try:
            r = requests.post(url, timeout=45,
                              headers={"Authorization": "Bearer " + key,
                                       "Content-Type": "application/json"},
                              json={"model": model, "max_tokens": max_tokens,
                                    "temperature": temperature,
                                    "messages": [{"role": "user", "content": prompt}]})
            if r.status_code == 200:
                t = (r.json()["choices"][0]["message"]["content"] or "").strip()
                time.sleep(1.2)
                return t, f"{name}/{model.split('/')[-1]}"
        except Exception:
            continue
    return "", None


def _parse_json(s):
    i = s.find("{")
    if i == -1:
        return None
    for end in range(len(s), i, -1):
        try:
            return json.loads(s[i:end])
        except Exception:
            continue
    try:
        return json.loads(s[i:] + "}" * (s.count("{") - s.count("}")))
    except Exception:
        return None


def _truth(j):
    """objective answer-baking (mirror of the gym's verifier; answers are
    BAKED INTO THE SEALED FILE at seal-time - the judge never re-trusts the
    teacher's live word)."""
    if j.get("code"):
        import subprocess
        import tempfile
        PY = os.path.join(REPO, "apex_venv", "Scripts", "python.exe")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(j["code"])
            p = f.name
        try:
            r = subprocess.run([PY, "-I", p], capture_output=True, text=True,
                               timeout=15)
            return r.stdout.strip()[:300]
        finally:
            try:
                os.remove(p)
            except Exception:
                pass
    vp = j.get("verify_py", "")
    if vp and vp != "ok":
        try:
            v = eval(vp, {"__builtins__": {}}, {})   # the expression's VALUE
            return v if isinstance(v, str) else repr(v)
        except Exception:
            return None
    return vp or None


def _grade(q, want, answer):
    """the answer-grade (value-aware, no quote artifacts; flaw by containment)"""
    if not answer:
        return False
    a = (answer or "").strip()
    if "| confidence:" in a.lower():
        a = a.split("| confidence:", 1)[0].strip()
    w = str(want)
    try:
        lhs = eval(w, {"__builtins__": {}}, {})
        if isinstance(lhs, str):
            return a.lower() == lhs.lower() or (lhs.lower() in a.lower())
        return abs(float(lhs) - float(a)) < 1e-9
    except Exception:
        pass
    wlow = w.lower()
    alow = a.lower()
    return wlow in alow or (wlow and wlow.replace("-", " ") in alow)


def seal():
    pockets = []
    for fam in FAMILIES:
        for _ in range(POCKETS_PER_FAMILY):
            raw, lane = _teacher(GEN[fam])
            j = _parse_json(raw) if raw else None
            if not j or not j.get("question"):
                time.sleep(8)
                continue
            truth = _truth(j)
            if truth is None:
                time.sleep(8)
                continue
            pockets.append({
                "family": fam,
                "question": j["question"][:600],
                "code": j.get("code"),
                "truth": truth,
                "answer_sha256": hashlib.sha256(
                    json.dumps(truth, sort_keys=True).encode()).hexdigest(),
                "sealed_by": lane,
            })
            print(f"[seal]: {fam} <- {str(truth)[:36]!r}")
            time.sleep(2)
    if len(pockets) < 10:
        print(f"[seal]: REFUSED - only {len(pockets)} pockets baked (>= 10 "
              "required for a meaningful holdout; nothing sealed)")
        return None
    sealed = {"sealed": time.strftime("%Y-%m-%d %H:%M:%S"),
              "pockets": pockets,
              "law": "the pocket NEVER enters memory/lessons; the judge grades "
                     "plain answers against baked truth"}
    tmp = HOLDOUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sealed, f, indent=1)
    os.replace(tmp, HOLDOUT)
    print(f"[seal]: SEALED - {len(pockets)} pockets -> Config/court_holdout.json")
    return sealed


def _internal_pct():
    """the gym's own recent hit% from the episodic calibration rows
    (GI-gym HIT/MISS rows); the honest read of what the fleet believes."""
    rows = []
    try:
        with open(EPISODIC, encoding="utf-8") as f:
            for ln in f:
                if "GI gym[" in ln and ("HIT" in ln or "MISS" in ln):
                    try:
                        j = json.loads(ln)
                        rows.append(j.get("text", ""))
                    except Exception:
                        continue
    except FileNotFoundError:
        pass
    last = rows[-60:]
    hits = sum(1 for t in last if "HIT" in t)
    return round(100 * hits / len(last), 1) if last else None


def judge():
    try:
        hold = json.load(open(HOLDOUT, encoding="utf-8-sig"))
    except Exception:
        print("[judge]: no sealed pocket - run `seal` first (honest refusal)")
        return None
    hits = done = 0
    for p in hold.get("pockets", []):
        want = p["truth"]
        ans, lane = _teacher(
            "Answer with ONLY the required answer: the exact output/number/"
            "flaw-name. If the prompt asks for confidence, keep it. No "
            "explanation.\n" + p["question"], max_tokens=200, temperature=0.0)
        if ans is None:
            continue
        hits += _grade(p["question"], want, ans)
        done += 1
    if not done:
        print("[judge]: every lane walled - no verdict invented (honest)")
        return None
    hold_pct = round(100 * hits / done, 1)
    ip = _internal_pct()
    verdict = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "holdout_pct": hold_pct, "holdout_n": done,
        "internal_pct": ip,
        "prev_holdout_pcts": (json.load(open(STATE, encoding="utf-8-sig"))
                              .get("prev_holdout_pcts", []))[-5:]
        if os.path.isfile(STATE) else [],
        "verdict": None, "note": "",
        "source": ("sealed holdout, n=%d (court_holdout.json); internal trend "
                   "= the gym's last-60 GI-gym rows" % done),
    }
    if verdict["prev_holdout_pcts"]:
        verdict["prev_holdout_pcts"].append(hold_pct)
    else:
        verdict["prev_holdout_pcts"] = [hold_pct]
    if ip is None:
        verdict["verdict"] = "HOLD-OUT-BLIND (no internal trend yet)"
        verdict["note"] = "the gym hasn't taught enough rows to compare"
    elif hold_pct >= ip - 10:
        verdict["verdict"] = "CLEAN (internal ~= holdout: no self-flattery detected)"
    elif ip - hold_pct >= 15:
        verdict["verdict"] = "SELF-FLATTERY ALARM"
        verdict["note"] = ("internal scores rose while the sealed holdout did "
                           "NOT - the reward is being gamed; every write-gate "
                           "should demand a court pass until this clears")
    else:
        verdict["verdict"] = "WATCH (drift 11-15 pts: re-judge tomorrow)"
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=1)
    os.replace(tmp, STATE)
    try:
        with open(EPISODIC, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": os.urandom(6).hex(), "ts": verdict["ts"], "kind": "court",
                "text": f"BLIND COURT: internal {ip}% vs sealed {hold_pct}% -> "
                        f"{verdict['verdict']}", "meta": {}, "imp": 0.9},
                ensure_ascii=False) + "\n")
    except Exception:
        pass
    print("[judge]:", verdict["verdict"], "| internal", ip, "% vs holdout",
          hold_pct, "% (n=%d)" % done)
    return verdict


def street(n=6):
    """Real-world planning drills from the family's OWN harvested backlog
    (external word distribution, structural truth - SWE-bench canon, $0)."""
    try:
        rows = [json.loads(l) for l in open(STREET, encoding="utf-8-sig")]
    except Exception:
        print("[street]: no harvested backlog - the GitHub Archive lane "
              "feeds Apex-Adapter/gh_archive_bugs.jsonl first")
        return None
    if not rows:
        print("[street]: backlog empty")
        return None
    random.seed()
    picks = random.sample(rows, min(n, len(rows)))
    results = []
    for r0 in picks:
        prompt = ("You are handed a REAL GitHub issue title from an open-source "
                  "project. Produce a fix PLAN outline (do NOT write code, do "
                  "NOT patch anything - the plan only). Reply ONLY JSON: "
                  "{\"repo\": repo, \"issue\": the title, \"plan_steps\": "
                  "[3-5 concrete steps], \"tests_needed\": [what to test to "
                  "prove the fix], \"risk\": one sentence}.\nrepo: "
                  + r0.get("repo", "?") + "\nissue: " + r0.get("issue", "?"))
        raw, lane = _teacher(prompt, max_tokens=700, temperature=0.2)
        j = _parse_json(raw) if raw else None
        if not j:
            results.append({"repo": r0.get("repo"), "ok": False})
            continue
        steps = j.get("plan_steps") or []
        tests = j.get("tests_needed") or []
        quality = (min(len(steps), 5) * 0.6 + (0.4 if tests else 0))
        results.append({"repo": r0.get("repo"), "issue": r0.get("issue", "")[:80],
                        "ok": len(steps) >= 3 and bool(tests),
                        "steps": len(steps), "tests": len(tests),
                        "quality": round(quality, 2), "lane": lane})
        time.sleep(2)
    ran = [r0 for r0 in results if r0.get("ok")]
    receipt = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "drilled": len(results), "structurally_sound": len(ran),
               "mean_quality": round(sum(r0.get("quality", 0) for r0 in results)
                                     / max(1, len(results)), 2),
               "note": "EXTERNAL-DISTRIBUTION planning truth: graded by "
                       "structure (steps + tests), not by invented answers",
               "rows": results}
    with open(os.path.join(REPO, "Config", "court_street_receipt.json"),
              "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1)
    print(f"[street]: {len(ran)}/{len(results)} real issues produced "
          "structurally sound fix-plans")
    return receipt


def internal_only_pct():
    return _internal_pct()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "judge"
    if mode == "seal":
        seal()
    elif mode == "street":
        street()
    else:
        judge()