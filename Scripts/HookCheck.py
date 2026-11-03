"""HookCheck v2.2 - THE NO-REPLACE GUARANTEE (2026-11-04).

Every deliberate upgrade of every round = a REQUIRED MARKER here; the list
only ever GROWS; the sentry re-checks all markers each fire (30-min repair
cooldown); missing markers = the honest alarm + an idempotent re-hook
(where a repair payload exists), never a wholesale rewrite.
Rounds recorded: the security/repair round, the fleet round, the GI round,
the memory round, the autonomy round, the outbound valve."""
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
CD = os.path.join(REPO, "Logs", "hookcheck_cooldown.txt")

REQUIRED = {
    "run_apex_evolution.py": ["hmac.compare_digest", "THE REPLAY CACHE", "THE RESEARCH",
                              "def deep_recall", "CONTAINER-ONLY EXECUTION",
                              'get("/dashboard")', "receipts_page.py"],
    "ApexMemory.py": ["EARNED-MEMORY", "RESURRECTION"],
    "ApexChatPage.html": ["authRefresh", "THE SELF-HEAL"],
    "Scripts/SkillUpgrader.py": ["THE HONESTY FIX"],
    "Scripts/FeedGrain.py": ["leads_sha256"],
    "Scripts/EarnLoop.py": ["ONCE-DAILY", "BOUNDED DIARY"],
    "Scripts/ApexUpward.py": ["briefs_filed"],
    "Scripts/TotalEvolution.py": ["_bf", "DE-SELF-REFERENCED"],
    "Scripts/GenePool.py": ["UNMEASURED-LINEAGE"],
    "Scripts/SwarmOrchestrator.py": ["CRASH-PROOF"],
    "Scripts/LaneGuard.py": ["pacer-parity fix"],
    "Scripts/ApexShard.py": ["LENGTH-AWARE TIMEOUT LADDER", "def _tier_timeout",
                             'STORM_BUDGET = {"protected"', "LaneBandit.update",
                             "DELEGATED TO THE SPINE", "HTTP 410"],
    "Scripts/LaneBandit.py": ["q_score", "seed_from_capability_map"],
    "Scripts/AutoRoster.py": ["retire_dead", "catalog_candidates"],
    "Scripts/WarmBrain.py": ["DEMAND-ADAPTIVE", "PIN_ORDER"],
    "Scripts/ApexIO.py": ["def env", "def atom", "def lock"],
    "Scripts/AnswerNorm.py": ["def match"],
    "Scripts/RealityCourt.py": ["def seal", "def judge", "def street", "AnswerNorm"],
    "Scripts/LocalGym.py": ["grade_brain", "AnswerNorm"],
    "Scripts/HorizonLadder.py": ["def measure"],
    "Scripts/LightResearch.py": ["def research", "def triggered"],
    "Scripts/SweSmoke.py": ["DockerCourt", "run_beat"],
    "Scripts/HookCheck.py": ["check_and_repair"],
    "receipts_page.py": ["local_mind", "horizon.json", "CanonCounts", "outcomes.json",
                         "blind court", "escape"],
    "Scripts/FilingBridge.py": ["def prepare", "def file", "GITHUB_TOKEN_CLASSIC", "DAY_CAP"],
    "Scripts/CertifyBridge.py": ["def certify", "NAME LAW"],
}

DREAM_HOOKS = """    try:
        import LocalGym as _lg
        _lg.grade_brain()
        _organ_notes.append("the serving floor graded on the sealed pocket")
    except Exception as _e_lg:
        m.record_event("local_mind", "local-gym skipped honestly: " + str(_e_lg)[:70])
    try:
        import Recall2 as _r2
        _r2.append_delta()
        _organ_notes.append("recall2 index delta-applied")
    except Exception:
        pass
    try:
        import HorizonLadder as _hl
        _hl.measure()
        _organ_notes.append("the autonomy horizon measured")
    except Exception as _e_hl:
        m.record_event("horizon", "ladder skipped honestly: " + str(_e_hl)[:70])
    try:
        import CertifyBridge as _cb
        _n = _cb.certify()
        _organ_notes.append(f"certify-bridge earned {len(_n)} execution-seats")
    except Exception as _e_cb:
        m.record_event("certification", "certify-bridge skipped honestly: " + str(_e_cb)[:70])
    try:
        import FilingBridge as _fb
        _doc = _fb.prepare()
        _organ_notes.append(f"filing-batch prepared ({_doc.get('batch_size', 0)} rows)")
    except Exception as _e_fb:
        m.record_event("filing_bridge", "filing-bridge skipped honestly: " + str(_e_fb)[:70])
"""

RECEIPTS_HOOKS = (
    "    lm = _json(os.path.join(R, \"Config\", \"local_mind.json\"))\n"
    "    if lm:\n"
    "        yard += (f\"<div class='kv'>the serving floor: <b>{_esc(lm.get('brain'))}</b> \"\n"
    "                 f\"scored <b>{_esc(lm.get('acc'))}%</b> on the SAME sealed \"\n"
    "                 f\"pocket ({_esc(lm.get('n'))} drills, same ruler) - the \"\n"
    "                 f\"fallback's real capability, published</div>\")\n"
    "    hz = _json(os.path.join(R, \"Config\", \"horizon.json\"))\n"
    "    if hz:\n"
    "        yard += (f\"<div class='kv'>the autonomy horizon: <b>{_esc(hz.get('steps'))} \"\n"
    "                 f\"steps/{_esc(hz.get('minutes'))} min</b> at \"\n"
    "                 f\"{_esc(hz.get('completion'))} completion ({_esc(hz.get('trend'))}) - \"\n"
    "                 f\"the METR-analog from the family's own ledgers</div>\")\n\n"
)

REPAIRS = {
    "Scripts/ApexDream.py": (
        'm.record_event("training", "night organs: " + ", ".join(_organ_notes))',
        DREAM_HOOKS),
    "receipts_page.py": (
        'return HTMLResponse(f"""<!doctype html>',
        RECEIPTS_HOOKS),
}


def check_and_repair():
    try:
        if os.path.exists(CD):
            last = open(CD, encoding="utf-8").read().strip()
            if time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S")) < 1800:
                return "cooldown"
    except Exception:
        pass
    repaired, alarmed, green = [], [], 0
    for rel, mts in REQUIRED.items():
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            continue
        try:
            t = open(p, encoding="utf-8-sig").read()
        except Exception:
            continue
        missing = [mk for mk in mts if mk not in t]
        if not missing:
            green += len(mts)
            continue
        if rel in REPAIRS:
            anchor, insert = REPAIRS[rel]
            if len(missing) >= len(mts) * 0.6:
                idx = t.find(anchor)
                if idx != -1:
                    t2 = t[:idx] + insert + t[idx:]
                    tmp = p + ".hookcheck.tmp"
                    with open(tmp, "w", encoding="utf-8", newline="") as f:
                        f.write(t2)
                    os.replace(tmp, p)
                    repaired.append(f"{rel}: hooks re-installed ({len(missing)} markers back)")
                    green += len(mts) - len(missing)
                    continue
        alarmed.append(f"{rel}: MISSING ({missing[0][:42]}...) - needs a deliberate repair")
    if repaired or alarmed:
        try:
            with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                      encoding="utf-8") as f:
                f.write(json.dumps({"id": os.urandom(6).hex(),
                                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "kind": "hookcheck",
                                    "text": "TRIPWIRE: " + "; ".join(
                                        repaired + alarmed)[:400],
                                    "meta": {}, "imp": 0.9},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
        with open(CD, "w", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    for r0 in repaired:
        print("[tripwire]", r0)
    for a0 in alarmed:
        print("[tripwire ALARM]", a0)
    return {"green": green, "repaired": len(repaired), "alarmed": len(alarmed)}


if __name__ == "__main__":
    r0 = check_and_repair()
    print("[tripwire]:", r0)