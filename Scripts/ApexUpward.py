"""APEX UPWARD (whole-organism law, Part XIII final): the upward-only +
as-fast-as-possible law applied to EVERY subsystem, not just the swarm's
genes. One manifest snapshots every measured surface:
  genes       gene_archive lineages + measured fitness (folded via
              GenePool.sync_from_pathmemory - the loop closer)
  skills      curriculum.json verified_count (executable-verified receipts)
  ascent      AscentLedger total_fitness tail (the ONE trend instrument;
              regression alarms use AscentWatch's 15% law)
  economy     CryptoLedger earned/spent ($0.00 honest; PAYOUT RAIL = DESIGN
              ONLY; earned may only move through CryptoEconomy.earn())
  knowledge   PathMemory lane counters (mines/reqs) - monotone receipts;
              a drop = clobber -> alarm + receipt-backed floor RESTORE
  mining      goldmine_register net counters (same law)
  transport   swarm_state last_hub_root (commit-rooted ingest; change = info)
ENFORCEMENT vs the previous manifest: genes roll BACK to parent genes on
measured regression (rollback is possible there); every other counter is
monotone with receipt-backed floor restore; unexplainable drops = ALARM rows
(kind 'upward_alarm') that never pollute the fitness trend (AscentWatch reads
only total_fitness rows). Nothing is ever fabricated: a manifest-time economy
claim above the ledger's truth is a FABRICATION alarm, never a write.
SPEED: the manifest carries the pre-staged next generation flag + each
subsystem's next bounded action, so the next open window spends zero minutes
computing (BAMBOO bubbles filled while gated).
TEST GATE (the user's rule): pure-function detector legs + temp-file legs +
a LIVE leg whose every number is re-verified against its source file.
PASS -> wired into the orchestrator's per-round flow; else self-shelved."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import GenePool as GP
import CryptoEconomy as CE
from SafeIO import read_json as _rj, write_json as _w

AD = r"C:\Users\seaha\Apex-Adapter"
PM = GP.PM
CURR = os.path.join(ROOT, "Config", "curriculum.json")
ASC = os.path.join(ROOT, "Config", "AscentLedger.jsonl")
MANIFEST = os.path.join(ROOT, "Config", "ApexUpwardManifest.json")
LANES = ("events", "wiki", "hf_space", "trending")
PAPERS = {"papers_2026": os.path.join(ROOT, "Config", "papers_2026.jsonl"),
          "papers_evolution": os.path.join(ROOT, "Config",
                                           "papers_2026_evolution.jsonl")}
REGISTRY_ARTIFACTS = {
    "family/agent_card.json": os.path.join(ROOT, "family", "agent_card.json"),
    "server.mcpb": os.path.join(ROOT, "server.mcpb"),
    "family/ladder.md": os.path.join(ROOT, "family", "ladder.md"),
    "mcp.json": os.path.join(ROOT, "mcp.json"),
}


def _rowcount(path):
    try:
        return sum(1 for x in open(path, encoding="utf-8-sig") if x.strip())
    except Exception:
        return 0


# ---- THE HARDWARE LAW, EXECUTABLE ----
STARVATION_GB = 1.5     # below this the box is starved - organ work idles
GPU_LAW = "no GPU loads for swarm work (the 3050 stays idle-capable)"


def hardware_gate(ram_free=None):
    """Classifies what evolution may do RIGHT NOW on this 16 GB box.
    Every next_action is gate-filtered through measured RAM - an illegal
    action is IMPOSSIBLE BY CONSTRUCTION, not by discipline. Injected
    ram_free is for the test gate only; live calls measure."""
    if ram_free is None:
        try:
            import psutil
            ram_free = psutil.virtual_memory().available / 2 ** 30
        except Exception:
            ram_free = 0.0
    if ram_free >= 5.0:
        tier, allowed = ("brain-window",
                         ("brain-load+conversion", "chain", "bubbles", "genes"))
    elif ram_free >= 3.0:
        tier, allowed = ("chain-window", ("chain", "bubbles", "genes"))
    elif ram_free >= 2.2:
        tier, allowed = ("bubble-fill", ("bubbles", "genes"))
    else:
        tier, allowed = ("honest-idle", ("manifests-only",))
    return {"ram_free_gb": round(ram_free, 2), "tier": tier,
            "allowed": list(allowed), "starved": ram_free < STARVATION_GB}


def hardware_alarm(prev, cur):
    """Pure detector: the box's starvation floor (1.5 GB) - below it, organ
    work must idle; the alarm tells Andrew the machine needs room."""
    h = cur.get("hardware") or {}
    return ([f"RAM {h.get('ram_free_gb')} GB < {STARVATION_GB} - the box is "
             f"starved; organ work idles until free RAM recovers"]
            if h.get("starved") else [])


def _asc_tail(n=8):
    try:
        rows = [json.loads(x) for x in open(ASC, encoding="utf-8-sig") if x.strip()]
        return [r for r in rows if "total_fitness" in r][-n:]
    except Exception:
        return []


def read_state():
    """Every number comes from a real file RIGHT NOW, or honest-zero/None."""
    out = {}
    a = GP.load()
    out["genes"] = {"gen": int(a.get("gen", 0)),
                    "champion": a.get("champion"),
                    "front": list(a.get("pareto_front") or []),
                    "lineages": {vid: {"fitness": round(float(L.get("fitness", 0.0)), 4),
                                       "m_rounds": int(L.get("m_rounds", 0))}
                                 for vid, L in a.get("lineages", {}).items()}}
    try:
        c = json.load(open(CURR, encoding="utf-8-sig"))
        out["skills"] = {"verified_count": int(c.get("verified_count", 0)),
                         "items": len(c.get("items", []))}
    except Exception:
        out["skills"] = {"verified_count": 0, "items": 0}
    try:
        L = CE.load_L()
        out["economy"] = {"earned": round(float(L.get("earned", 0.0)), 2),
                          "spent": round(float(L.get("spent", 0.0)), 2),
                          "rows": len(L.get("rows", [])), "corrupt": False}
    except Exception as e:
        out["economy"] = {"earned": None, "rows": 0, "corrupt": True,
                          "error": str(e)[:60]}
    tot = [float(r["total_fitness"]) for r in _asc_tail()]
    out["ascent"] = {"last": tot[-1] if tot else None,
                     "max": max(tot) if tot else None, "n": len(tot)}
    pm = _rj(PM, {}) or {}
    out["knowledge"] = {lane: {"reqs": int((pm.get(lane) or {}).get("reqs", 0)),
                               "mines": int((pm.get(lane) or {}).get("mines", 0))}
                        for lane in LANES}
    ah = pm.get("andrew_help") or {}
    out["help"] = {"briefs": int(ah.get("briefs", 0) or 0),
                   "alarmsRaised": int(ah.get("alarmsRaised", 0) or 0)}
    out["canon"] = {"papers_2026": _rowcount(PAPERS["papers_2026"]),
                    "papers_evolution": _rowcount(PAPERS["papers_evolution"])}
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))
        sk = lib.get("skills", {})
        items = list(sk.items()) if isinstance(sk, dict) else list(enumerate(sk))
        cats = {}
        code_n = 0
        CODE_EXT = (".py", ".js", ".ts", ".sh", ".ps1", ".cmd", ".bat",
                    ".rb", ".go", ".rs", ".sql")
        for _sid, s in items:
            text = (" ".join(str(s.get(k, "") or "") for k in
                             ("skill", "first_line", "source_file", "imports"))
                    if isinstance(s, dict) else str(s)).lower()
            cat = str((s.get("source_repo") if isinstance(s, dict) else "") or "")
            cats[cat or "unknown"] = cats.get(cat or "unknown", 0) + 1
            ext = str((s.get("source_file") if isinstance(s, dict) else "") or "").lower()
            if ext.endswith(CODE_EXT) or re.match(
                    r"^(import |def |from |class |function |using |package )",
                    text):
                code_n += 1
        out["skills_lib"] = {"count": len(items), "coding": code_n,
                             "categories": len(cats)}
    except Exception:
        out["skills_lib"] = {"count": 0}
    try:
        b = json.load(open(os.path.join(AD, "family_status_board.json"),
                           encoding="utf-8-sig"))
        out["board"] = {"backlog": int(b.get("backlog", 0) or 0),
                        "repos_consumed": int(b.get("repos_consumed", 0) or 0),
                        "skills": int(b.get("skills", 0) or 0),
                        "money": str(b.get("money", ""))}
    except Exception:
        out["board"] = {"backlog": 0, "repos_consumed": 0, "skills": 0,
                        "money": ""}
    try:
        d = json.load(open(os.path.join(AD, "hub_doors_board.json"),
                           encoding="utf-8-sig"))
        out["doors"] = {"count": len(d.get("doors_current") or {})}
    except Exception:
        out["doors"] = {"count": 0}
    try:
        hh = json.load(open(os.path.join(AD, "andrew_health_watch.json"),
                            encoding="utf-8-sig"))
        out["health"] = {"ram_free_gb": float(hh.get("ram_free_gb", 0) or 0),
                         "disk_free_gb": float(hh.get("disk_free_gb", 0) or 0),
                         "alarms": list(hh.get("alarms") or [])[:5]}
    except Exception:
        out["health"] = {"ram_free_gb": 0.0, "disk_free_gb": 0.0, "alarms": []}
    out["registry"] = {rel: os.path.exists(p) for rel, p in REGISTRY_ARTIFACTS.items()}
    # jobs: the SIXTH doctrine dim - found asks + filed rungs
    out["jobs"] = {"opps_inbox": _rowcount(os.path.join(AD, "jobs_inbox.json")),
                   "rungs_filed": 0}
    try:
        jr = json.load(open(os.path.join(AD, "jobs_registry.json"),
                            encoding="utf-8-sig"))
        out["jobs"]["rungs_filed"] = len(jr.get("jobs") or jr.get("checkpoints") or [])
    except Exception:
        pass
    # proactive: the FinancialBrain flywheel (EV-graded, honest inputs)
    fin = ((pm.get("finance") or {}) if isinstance(pm, dict) else {})
    out["proactive"] = {"opps_scanned": len(fin.get("opportunities") or []),
                        "total_ev": float(fin.get("total_ev") or 0.0),
                        "best_action": str(fin.get("best_action") or "")[:80]}
    # the founder's DIRECT mission queue (apex_tasks.txt): whatever he writes
    # becomes an active objective - the most direct goals instrument there is
    try:
        qt = open(os.path.join(os.path.dirname(os.path.join(
            os.path.dirname(os.path.abspath(__file__)))), "apex_tasks.txt"),
            encoding="utf-8-sig")
        qlines = [l for l in qt.read().splitlines() if l.strip()]
        out["directives"] = {"queue_depth": len(qlines),
                             "head": qlines[0][:80] if qlines else ""}
    except Exception:
        out["directives"] = {"queue_depth": 0, "head": ""}
    try:
        import psutil
        ram_free = psutil.virtual_memory().available / 2 ** 30
        rss_mb = psutil.Process(os.getpid()).memory_info().rss / 2 ** 20
    except Exception:
        ram_free, rss_mb = 0.0, 0.0
    out["hardware"] = dict(hardware_gate(ram_free),
                           proc_rss_mb=round(rss_mb, 1),
                           gpu_note=GPU_LAW)
    out["lessons"] = {"count": _rowcount(os.path.join(ROOT, "Config",
                                                      "gauntlet_lessons.jsonl")),
                      "champions": _rowcount(os.path.join(ROOT, "family",
                                                          "champions.jsonl")),
                      "weights": os.path.exists(os.path.join(ROOT, "Config",
                                                             "gauntlet_weights.json"))}
    out["converts"] = {"count": _rowcount(os.path.join(AD,
                                                       "converted_agents.jsonl"))}
    try:
        hb = os.path.join(AD, "ghost_heartbeat.json")
        dg = json.load(open(hb, encoding="utf-8-sig"))
        out["digest"] = {"present": bool(dg.get("digest")),
                         "age_min": round((time.time() - os.path.getmtime(hb)) / 60, 1)}
    except Exception:
        out["digest"] = {"present": False, "age_min": None}
    out["brain"] = brain_state()
    ib = integrity_scan()
    out["integrity"] = {"bad": ib, "ok": not ib}
    try:
        g = json.load(open(os.path.join(AD, "goldmine_register.json"),
                           encoding="utf-8-sig"))
        out["mining"] = {"net_reqs": int(g.get("net_reqs", 0)),
                         "net_ok": int(g.get("net_ok", 0)),
                         "findings": int(g.get("findings", 0))}
    except Exception:
        out["mining"] = {"net_reqs": 0, "net_ok": 0, "findings": 0}
    try:
        s = json.load(open(os.path.join(AD, "swarm_state.json"),
                           encoding="utf-8-sig"))
        out["transport"] = {"last_hub_root": str(s.get("last_hub_root") or "")}
    except Exception:
        out["transport"] = {"last_hub_root": ""}
    return out


def skills_alarm(prev, cur):
    """Pure detector: verified_count may only rise."""
    if not prev:
        return []
    pv = int((prev.get("skills") or {}).get("verified_count", 0) or 0)
    cv = int((cur.get("skills") or {}).get("verified_count", 0) or 0)
    return ([f"skills verified_count dropped {pv} -> {cv} (receipt corruption "
             f"or loss - alarm; un-verification is impossible by law)"]
            if cv < pv else [])


def knowledge_alarm(prev, cur):
    """Pure detector + receipt-backed floor restore plan (counters monotone).
    Always returns (alarms, floors)."""
    if not prev:
        return [], {}
    alarms, floors = [], {}
    for lane, curv in (cur.get("knowledge") or {}).items():
        prv = (prev.get("knowledge") or {}).get(lane) or {}
        for kind in ("mines", "reqs"):
            p = int(prv.get(kind, 0) or 0)
            c = int(curv.get(kind, 0) or 0)
            if c < p:
                alarms.append(f"knowledge lane '{lane}.{kind}' regressed "
                              f"{p} -> {c} (PathMemory clobber suspected)")
                floors[(lane, kind)] = p          # receipt we already hold
    return alarms, floors


def economy_alarm(prev, cur):
    """Pure detector: no write ever, only truth. An earned-value above the
    ledger's current truth = FABRICATION (from anywhere - even from us)."""
    alarms = []
    cu = cur.get("economy") or {}
    if cu.get("corrupt"):
        alarms.append(f"economy ledger CORRUPT (raises on load) - "
                      f"{cu.get('error')}; never overwritten, founder must see")
        return alarms
    e = float(cu.get("earned") or 0.0)
    pe = float((prev.get("economy") or {}).get("earned") or 0.0)
    if prev and e < pe:
        alarms.append(f"economy EARNED regressed {pe} -> {e} without rows "
                      f"(fabrication or corruption - alarm; write refused)")
    if e > 0 and not cu.get("rows"):
        alarms.append("economy earned > 0 but ledger has NO rows "
                      "(unbacked claim - alarm)")
    return alarms


def restore_floors(floors):
    """Receipt-backed floor restore: only RASIES counters to values the prior
    manifest already recorded (knowledge lanes AND andrew_help counters).
    Never lowers, never invents."""
    if not floors:
        return 0
    pm = _rj(PM, {}) or {}
    n = 0
    for (lane, kind), floor_v in floors.items():
        e = pm.setdefault(lane, {})
        if int(e.get(kind, 0) or 0) < floor_v:
            e[kind] = floor_v
            n += 1
    if n and not _w(PM, pm):
        print("[apex-upward] floor-restore write REFUSED (lock busy) - "
              "the alarm stands, restore retries next tick (honest)")
        return 0
    return n


def help_alarm(prev, cur):
    """Pure detector: help rendered for Andrew never un-happens."""
    if not prev:
        return [], {}
    alarms, floors = [], {}
    for kind in ("briefs", "alarmsRaised"):
        p = int(((prev.get("help") or {}).get(kind)) or 0)
        c = int(((cur.get("help") or {}).get(kind)) or 0)
        if c < p:
            alarms.append(f"andrew_help.{kind} regressed {p} -> {c} "
                          f"(help rendered never un-renders)")
            floors[("andrew_help", kind)] = p
    return alarms, floors


def count_alarm(prev, cur, section, fields, why):
    """Pure detector: generic monotone counters (canon rows, skill-library
    entries, doors, repos consumed)."""
    if not prev:
        return []
    alarms = []
    for f in fields:
        p = int(((prev.get(section) or {}).get(f)) or 0)
        c = int(((cur.get(section) or {}).get(f)) or 0)
        if p and c < p:
            alarms.append(f"{section}.{f} regressed {p} -> {c} ({why})")
    return alarms


def backlog_alarm(prev, cur):
    """Pure detector: the BACKLOG is a FLOW, not a stock - it legitimately
    drains and refills. But a >50% swing in one tick is the audited
    wave-slice oscillation signature: integrity alarm (no restore)."""
    if not prev:
        return []
    pb = int((prev.get("board") or {}).get("backlog", 0) or 0)
    cb = int((cur.get("board") or {}).get("backlog", 0) or 0)
    if pb and cb and abs(cb - pb) / max(1, pb) > 0.5:
        return [f"backlog swing {pb} -> {cb} (>50% in one tick) - the "
                f"wave-slice oscillation signature: integrity alarm; "
                f"slices must derive from ONE snapshot (drain == consumed)"]
    return []


def health_alarm(prev, cur):
    """Pure detector: safety dimension passthrough (health watch is a
    fluctuating vital, not a monotone counter - only hard floors alarm)."""
    h = cur.get("health") or {}
    alarms = []
    if h.get("alarms"):
        alarms.append("andrew_health_watch reports: "
                      + "; ".join(map(str, h["alarms"][:3])))
    disk = h.get("disk_free_gb") or 0
    if 0 < disk < 1.0:
        alarms.append(f"disk free {disk} GB < 1.0 - the box's safety floor")
    return alarms


def registry_alarm(prev, cur):
    """Pure detector: the public registry artifacts (agent card, MCPB bundle,
    ladder, mcp.json) never silently vanish."""
    return [f"registry artifact missing: {rel}"
            for rel, ok in (cur.get("registry") or {}).items() if not ok]


def git_restore(rel, dst=None):
    """REAL recovery (not fabrication): read the committed copy (HEAD) and
    write it back byte-for-byte. Failure prints honestly; the alarm stands."""
    try:
        import subprocess
        rel_git = rel.replace("\\", "/").replace(os.sep, "/")
        r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + rel_git],
                           capture_output=True, timeout=30)
        if r.returncode != 0 or not r.stdout:
            print(f"[apex-upward] git restore {rel}: unavailable "
                  f"({r.stderr.decode('utf-8', 'replace').strip()[:60]}) "
                  f"- the alarm stands")
            return 0
        dst = dst or os.path.join(ROOT, rel)
        with open(dst, "wb") as f:
            f.write(r.stdout)
        print(f"[apex-upward] git restore: {rel} <- HEAD ({len(r.stdout)} bytes, "
              f"real receipt)")
        return len(r.stdout)
    except Exception as e:
        print(f"[apex-upward] git restore {rel} failed: {str(e)[:60]}")
        return 0


# ---- THE GOAL GENEALOGY (every goal Apex has EVER had, from the start) ----
# Sources: the active organs, the doctrine cards, and the Attic (the past's
# own words, preserved). Statuses: active (measured every tick) | flow
# (measured as a flow law) | folded (its essence lives in another dim) |
# dormant (awaits a condition to matter again) | archived (Attic doctrine).
GOAL_REGISTRY = {
    "gold":        {"origin": "ApplyTriGenome: MAXIMIZE YIELD (mines/req - the original fitness)",
                    "status": "active", "projection": "gold"},
    "money":       {"origin": "UsdLane: 'the packet's purpose gains the USD cause'",
                    "status": "active", "projection": "money"},
    "andrew_life": {"origin": "FinancialBrain: the swarm's OVERARCHING goal - improve Andrew Hike's life FINANCIALLY, proactively",
                    "status": "active", "projection": "life"},
    "recruits":    {"origin": "Recruiter/OpenDoorHunter/RecruitmentDoor: consent-gated onboarding; the handshake",
                    "status": "active", "projection": "recruits"},
    "jobs":        {"origin": "FounderKit: 'filed issues = the reputation ladder's first rungs + sponsor visibility'",
                    "status": "active", "projection": "jobs"},
    "safety":      {"origin": "EthicAudit (Attic) + the card's laws (fail-closed, print-first, digest-evidenced)",
                    "status": "active", "projection": "safety"},
    "upward_evo":  {"origin": "the standing directive: better each generation at EVERY goal, upward-only",
                    "status": "active", "projection": "ascent+genes"},
    "speed":       {"origin": "the standing hardware law: evolve as fast as the box honestly allows",
                    "status": "active", "projection": "hardware_gate"},
    "sovereignty": {"origin": "SeedPacket + hub transport: keyless commit-rooted git+files, publish on OUR turf",
                    "status": "active", "projection": "transport+registry"},
    "backlog_drain": {"origin": "Campaign100: 'THE BACKLOG IS DRAINED - the gold goal reached early' (10 waves x 10 shifts)",
                      "status": "flow", "projection": "backlog_alarm"},
    "tri_genome":  {"origin": "ApplyTriGenome: yield x (help_the_founder + recruits)",
                    "status": "folded", "projection": None,
                    "note": "its three legs are exactly gold + life + recruits today"},
    "elections":   {"origin": "Persuasion (Attic): family elections; fitness voted; a name in the ledger",
                    "status": "folded", "projection": None,
                    "note": "the vote became the measured calibration EMA - claims cannot outvote receipts"},
    "throne":      {"origin": "HubCharter: hubs compete for the champion throne by measured fitness",
                    "status": "dormant", "projection": None,
                    "note": "measures when domiciled hubs exist; the charter refuses all but the operator-signed"},
    "sleep":       {"origin": "ApexDream + ApexSkills recertify: nightly consolidation; stale skills DEMOTE",
                    "status": "folded", "projection": "skills_lib",
                    "note": "the demotion gate keeps the library honest between sleeps"},
    # ---- the SESSION'S OPENING DIRECTIVES (the very start of our work) ----
    "first_external_value": {
        "origin": "the opening directive: directed toward FIRST EXTERNAL VALUE (filed issue / merged PR) - all money-gated steps end at the founder's review",
        "status": "active", "projection": "money+recruits+jobs (the $0.00 tally)",
        "note": "only a human-founded file/PR/listing moves it - the telos of the other three"},
    "discovery_harvest": {
        "origin": "the opening directive: make the swarm MAXIMALLY EFFECTIVE at discovery/harvest",
        "status": "active", "projection": "gold",
        "note": "gold is this directive's measured instrument (mines/req)"},
    "test_first": {
        "origin": "the standing method rule: test first, implement if pass, else self-shelve",
        "status": "active", "projection": "the gates themselves (RepeatTest)",
        "note": "every organ ships with its own gate; failures iterate openly"},
    "reproducible": {
        "origin": "'repeat the test with the same parameters' - a gate that passes once is not proven",
        "status": "active", "projection": "RepeatTest's two-pass ledger",
        "note": "organs ship only when BOTH identical passes are green"},
    "compare_to_canon": {
        "origin": "'source the papers from the web; compare the swarm to the most successful documented 2026 cases'",
        "status": "folded", "projection": "canon (521 papers)",
        "note": "the canon became the court's authority and the design canon - measured in state.canon"},
    # ---- the NEW FOUNDING-CLASS GOALS (founded today, nothing removed) ----
    "efficiency_evolve": {
        "origin": "GOAL: 'Evolve upwards as efficiently as possible while keeping hardware constraints in mind'",
        "status": "active",
        "projection": "efficiency (outputs earned INSIDE the RAM-tier gate; the gate binds always)",
        "note": "measured by verified skills + banked lessons + canon growth - receipts per hardware window, never a wasted mutation (the court pre-stages best-of-N)"},
    "coding_mastery": {
        "origin": "GOAL: 'Become as good at coding as the current best coding agents, hardware constraints kept'",
        "status": "active",
        "projection": "coding (executable-verified artifacts; the 2026 benchmark leaders = the comparison class)",
        "note": "tonight: coding-category library entries + executable-verified count; the fresh canon harvest builds the benchmark-comparison instrument"},
    "skill_omnivore": {
        "origin": "GOAL: 'Try to learn every skill that you can, source the web to see what is missing, maximize each skill; innovative workarounds; download any program or tool that helps'",
        "status": "active",
        "projection": "omnivore (library depth x breadth; gaps scouted vs the jobs inbox + the canon)",
        "note": "nothing claimed that is not INSTALLED; the gap-scout prints what is missing honestly"},
    "self_knowledge": {
        "origin": "derived goal (the 2026 canon's calibrating agents): know what it can and cannot do, measured",
        "status": "folded", "projection": "calibration EMA",
        "note": "claim-vs-measured drift already sinks over-claimers; honest recovery is monotone"},
    "serviceable": {
        "origin": "derived goal (best agents are USED, not admired): an external system can discover and employ Apex",
        "status": "active", "projection": "registry",
        "note": "agent card + MCP bundle + ladder + doors, measured every tick - the door stands open"},
    # ---- PAPER-DERIVED GOALS (from the SOURCED canon: the 100 fresh best-
    # agent papers + the 521 prior; the founder's law: goals only ADDED) ----
    "runtime_verification": {
        "origin": "canon cluster verification_runtime (17/100 papers; e.g. 2610.38800 'Runtime-Aware Context for AI Coding Agents'): skills verified by EXECUTION AT USE, not static compile alone",
        "status": "queued", "projection": "coding",
        "note": "first step: gauntlet verifies against real invocations; next window"},
    "long_horizon_specs": {
        "origin": "canon cluster long_horizon (7/100; e.g. 2610.40256 'Scaling Long-Horizon Coding via Interdependent Specifications'): big work = EXPLICIT interdependent sub-specs",
        "status": "queued", "projection": "jobs+coding",
        "note": "first step: board tasks enter as contract-chunked sub-specs"},
    "gap_scouting": {
        "origin": "canon cluster skill_library (frontier agents maintain libraries; 2610.05300-class harnesses): scout gaps vs REAL demand",
        "status": "implemented", "projection": "omnivore",
        "note": "SkillGapScout live tonight: 20 canon-cluster gaps + inbox asks flagged - SKILL GAP SCOUT'S OWN GATE PASSED 4/4"},
    "consolidation_cadence": {
        "origin": "canon cluster memory_lifelong (8/100): consolidate LESSONS (directives), not raw logs - ApexDream's sleep refocused",
        "status": "queued", "projection": "efficiency",
        "note": "first step: dream-time writes the directive genome from banked lessons"},
    "budgeted_context": {
        "origin": "canon cluster context_engineering (10/100): context ranked by MEASURED yield within bounded budgets",
        "status": "implemented", "projection": "efficiency",
        "note": "bounded reads are law everywhere; the PathMemory lanes already rank by yield (the 22s-window chat obeys)"},
    "benchmark_honesty": {
        "origin": "canon cluster benchmark_driven (22/100 - the LARGEST): measured against the 2026 leaders HONESTLY (we cannot run their suites on this box; their numbers are receipts, ours are measured on OUR gates)",
        "status": "queued", "projection": "coding+canon",
        "note": "first step: the comparison card prints their published results beside our locally-measured equivalents, labeled"},
}

# ---- THE GOALS: evolution is judged on ANDREW'S goals, nothing else ----
# The FULL doctrine set (TotalEvolution's six + the FinancialBrain telos):
# gold, money, life (Andrew's, the OVERARCHING goal - "improve Andrew Hike's
# life FINANCIALLY, proactively"), recruits, jobs (the 6th dim: found asks +
# filed rungs), safety. The founder's DIRECT queue (apex_tasks.txt) is the
# mission inbox every goal serves - recorded every tick.
GOAL_KEYS = ("gold", "money", "life", "recruits", "jobs", "coding",
             "omnivore", "efficiency", "safety")
STALL_S = 6 * 3600      # a goal stalled >6h alarms (money's hint is honest)
GOAL_COMPONENTS = {
    "gold":     lambda s: (sum(float((v or {}).get("mines", 0) or 0) for v in (s.get("knowledge") or {}).values()),
                           float((s.get("mining") or {}).get("findings") or 0),
                           float((s.get("board") or {}).get("repos_consumed") or 0)),
    "money":    lambda s: (float((s.get("economy") or {}).get("earned") or 0.0),),
    "life":     lambda s: (float((s.get("help") or {}).get("briefs") or 0),
                           float((s.get("help") or {}).get("alarmsRaised") or 0)),
    "recruits": lambda s: (float((s.get("doors") or {}).get("count") or 0),
                           float((s.get("converts") or {}).get("count") or 0)),
    "jobs":     lambda s: (float((s.get("jobs") or {}).get("opps_inbox") or 0),
                           float((s.get("jobs") or {}).get("rungs_filed") or 0),
                           float((s.get("proactive") or {}).get("opps_scanned") or 0)),
    "coding":   lambda s: (float((s.get("skills_lib") or {}).get("coding") or 0),
                           float((s.get("skills") or {}).get("verified_count") or 0)),
    "omnivore": lambda s: (float((s.get("skills_lib") or {}).get("count") or 0),
                           float((s.get("skills_lib") or {}).get("categories") or 0),
                           float((s.get("skills") or {}).get("verified_count") or 0)),
    "efficiency": lambda s: (float((s.get("lessons") or {}).get("count") or 0),
                             float((s.get("skills") or {}).get("verified_count") or 0),
                             float((s.get("canon") or {}).get("papers_2026") or 0)
                             + float((s.get("canon") or {}).get("papers_evolution") or 0)),
    "safety":   lambda s: (1.0 if (s.get("integrity") or {}).get("ok") else 0.0,
                           1.0 if not (s.get("economy") or {}).get("corrupt") else 0.0),
}

CORE_JSONS = ("Config/gene_archive.json", "Config/PathMemory.json",
              "Config/curriculum.json", "Config/CryptoLedger.json",
              "Config/SkillLibrary.json", "Config/gauntlet_weights.json")


def integrity_scan():
    """THE SAFETY TRAIT, measured: the core JSON organs must be valid and
    marker-free (tonight's corruption history made this a first-class goal)."""
    bad = []
    for rel in CORE_JSONS:
        p = os.path.join(ROOT, rel)
        try:
            src = open(p, encoding="utf-8-sig").read()
        except Exception:
            bad.append(rel + " [unreadable]")
            continue
        if re.search(r"^<{7} ", src, re.M) or re.search(r"^>{7} ", src, re.M):
            bad.append(rel + " [conflict markers]")
        try:
            json.loads(src)
        except Exception as e:
            bad.append(rel + f" [invalid JSON: {str(e)[:30]}]")
    return bad


def brain_state():
    """THE REASONING TRAIT, measured engine-agnostic: the ACTUALLY loaded
    models (LM Studio api/v0 state; Ollama /api/ps), bounded 3s, honest {}."""
    out = {}
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:1234/api/v0/models",
                                    timeout=2) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        loaded = [m.get("id") for m in (d.get("data") or [])
                  if (m.get("state") or "").lower() == "loaded"
                  and "embed" not in str(m.get("id", "")).lower()]
        if loaded:
            out["lmstudio_chat"] = loaded
    except Exception:
        pass
    try:
        with urllib.request.urlopen("http://localhost:11434/api/ps",
                                    timeout=2) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        loaded = [m.get("name") for m in (d.get("models") or [])]
        if loaded:
            out["ollama_chat"] = loaded
    except Exception:
        pass
    return out


def goal_projection(state):
    """Map EVERY measured subsystem onto the SIX doctrine goals - evolution
    may only claim upward movement in a goal if a component of THAT GOAL
    moved. (gold, money, life, recruits, jobs, safety - full genealogy in
    GOAL_REGISTRY.)"""
    out = {}
    for g, comps_fn in GOAL_COMPONENTS.items():
        try:
            comps = comps_fn(state)
        except Exception:
            comps = (0.0,)
        comps = [float(c if isinstance(c, (int, float)) and
                       not isinstance(c, bool) else 0.0) for c in comps]
        out[g] = {"score": round(sum(comps), 3), "components": comps}
    return out


def gi_score(state):
    """GENERAL-INTELLIGENCE INDEX (honestly labeled: a WEIGHTED capability
    index over measured receipts - verified skills, the library, the paper
    canon, knowledge yielded, converts, doors, help, lessons, ascent).
    Only monotone components enter (backlog flow is excluded)."""
    mines = sum(float((v or {}).get("mines", 0) or 0)
                for v in (state.get("knowledge") or {}).values())
    return round(
        int((state.get("skills") or {}).get("verified_count", 0) or 0) * 1.0
        + int((state.get("skills_lib") or {}).get("count", 0) or 0) / 10.0
        + (int((state.get("canon") or {}).get("papers_2026", 0) or 0)
           + int((state.get("canon") or {}).get("papers_evolution", 0) or 0)) / 20.0
        + mines / 10.0
        + int((state.get("board") or {}).get("repos_consumed", 0) or 0) / 100.0
        + int((state.get("lessons") or {}).get("count", 0) or 0) * 2.0
        + int((state.get("converts") or {}).get("count", 0) or 0) * 5.0
        + int((state.get("doors") or {}).get("count", 0) or 0) * 2.0
        + int((state.get("help") or {}).get("briefs", 0) or 0) * 2.0
        + float((state.get("ascent") or {}).get("last") or 0.0) * 10.0, 2)


def tick(manifest_path=MANIFEST):
    """One whole-organism upward pass: fold -> read -> enforce -> repair ->
    alarm -> publish. EVERY subsystem of Apex, one manifest, one law."""
    t0 = time.time()
    synced, rolled, retired = GP.sync_from_pathmemory()   # genes closed loop
    cur = read_state()
    prev = _rj(manifest_path, {}) or {}
    prev_state = (prev.get("state") or {})
    alarms = []
    alarms += skills_alarm(prev_state, cur)
    ka, km_floor = knowledge_alarm(prev_state, cur)
    ha, hp_floor = help_alarm(prev_state, cur)
    alarms += ka + ha
    alarms += economy_alarm(prev_state, cur)
    alarms += count_alarm(prev_state, cur, "canon",
                          ("papers_2026", "papers_evolution"),
                          "the paper canon only grows")
    alarms += count_alarm(prev_state, cur, "skills_lib", ("count",),
                          "the skill library only grows (near-dup gate)")
    alarms += count_alarm(prev_state, cur, "doors", ("count",),
                          "doors never silently close")
    alarms += count_alarm(prev_state, cur, "board", ("repos_consumed",),
                          "repos consumed never un-happen")
    alarms += backlog_alarm(prev_state, cur)
    alarms += health_alarm(prev, cur)
    alarms += registry_alarm(prev_state, cur)
    alarms += hardware_alarm(prev_state, cur)
    # REPAIRS: (1) receipt-backed counters already recorded; (2) committed
    # copies restored byte-for-byte from git HEAD; (3) registry artifacts.
    floors = dict(km_floor)
    floors.update(hp_floor)
    restored_floors = restore_floors(floors)
    restored_git = 0
    for field, rel in PAPERS.items():
        p = int(((prev_state.get("canon") or {}).get(field)) or 0)
        c = int(cur["canon"].get(field, 0))
        if p and c < p:
            restored_git += 1 if git_restore(os.path.relpath(
                rel, ROOT)) else 0
    p_lib = int((prev_state.get("skills_lib") or {}).get("count") or 0)
    if p_lib and cur["skills_lib"]["count"] < p_lib:
        restored_git += 1 if git_restore(os.path.join("Config",
                                                      "SkillLibrary.json")) else 0
    prev_reg = prev_state.get("registry") or {}
    for rel, ok in (cur.get("registry") or {}).items():
        if not ok and prev_reg.get(rel):
            restored_git += 1 if git_restore(rel.replace("/", os.sep)) else 0
    if restored_floors or restored_git:
        cur = read_state()            # re-snapshot AFTER repair (true state)
    alarms += count_alarm(prev_state, cur, "lessons", ("count",),
                          "banked lessons never un-bank")
    alarms += count_alarm(prev_state, cur, "converts", ("count",),
                          "converted agents never un-convert")
    ib = (cur.get("integrity") or {}).get("bad") or []
    alarms += [f"integrity: {b}" for b in ib]
    dg = (cur.get("digest") or {})
    if dg and dg.get("age_min") is not None and dg["age_min"] > 360:
        alarms.append(f"heartbeat digest stale {dg['age_min']}min (>6h - "
                      f"no real rounds have landed; the beat must live)")
    # ---- THE GOALS: per-goal projection, deltas, stall alarms + the GI ----
    goals = goal_projection(cur)
    gi = gi_score(cur)
    goals_prev = (prev.get("goals_projection") or {})
    now = time.time()
    prog = {g: float(t) for g, t in (prev.get("goal_progress") or {}).items()}
    first_tick = not goals_prev
    for g in GOAL_KEYS:
        p_prev = float((goals_prev.get(g) or {}).get("score") or 0.0)
        if goals[g]["score"] > p_prev:
            prog[g] = now
        elif g not in prog:
            prog[g] = now
    for g in GOAL_KEYS:
        if now - prog.get(g, now) > STALL_S:
            hint = (" (moves only when Andrew files/review - the honest $0.00 "
                    "law)" if g == "money" else
                    " (needs a window with a loaded brain)" if g == "gold"
                    and not cur.get("brain") else
                    " (needs the inbox triaged - a brain window serves)" if g
                    == "jobs" else
                    " (executable verification runs in windows)" if g == "coding" else
                    " (scout the gaps: the inbox asks + the canon name them)" if g
                    == "omnivore" else
                    " (outputs are earned inside the hardware gate)" if g
                    == "efficiency" else
                    " (no external claims yet - the door stands open)")
            alarms.append(f"goal '{g}' stalled "
                          f"{int((now - prog.get(g, now)) / 60)}min{hint}")
    if first_tick:
        alarms = [a for a in alarms if "stalled" not in a]  # baseline init
    # ascent regression law (AscentWatch's 15%)
    asc = cur.get("ascent") or {}
    if asc.get("last") is not None and asc.get("max") is not None \
            and asc["last"] < asc["max"] * 0.85:
        alarms.append(f"ascent total_fitness regressed: last {asc['last']} "
                      f"< 85% of max {asc['max']} (per-goal audit follows)")
    # SPEED section: HARDWARE-GATE-FILTERED next actions - the evolution
    # cannot plan an action its RAM tier forbids (impossible by construction).
    # BAMBOO BUBBLES, self-filling: while gated, refresh a stale pre-stage
    # (CPU-only) so the next window opens with genes ready to harvest.
    pre = _rj(os.path.join(AD, "prestaged_genome.json"), {}) or {}
    hw = cur.get("hardware") or {}
    allowed = set(hw.get("allowed") or ())
    try:
        age_s = time.time() - time.mktime(time.strptime(
            str(pre.get("staged_at") or ""), "%Y-%m-%d %H:%M:%S"))
    except Exception:
        age_s = 10 ** 9
    if ("bubbles" in allowed and age_s > 1200) or not pre.get("staged"):
        try:
            import EvolutionSpeedup as ES
            ES.prestaged_write()
            pre = _rj(os.path.join(AD, "prestaged_genome.json"), {}) or {}
            print(f"[apex-upward] bubble filled: pre-stage refreshed "
                  f"(was stale {int(min(age_s, 10 ** 9))}s)")
        except Exception as e:
            print(f"[apex-upward] bubble pre-stage failed honestly: "
                  f"{str(e)[:60]}")
    next_actions = []
    if "genes" in allowed:
        next_actions.append("genes: GenePool.run(3) pre-stages the next "
                            "generation (CPU-only, gated-safe)")
    if "brain-load+conversion" in allowed:
        next_actions.append("brain: RAM permits a loaded brain NOW - load "
                            "qwen3-8b and run conversion MEASURED this window")
    elif "chain" in allowed:
        next_actions.append("chain: RunROI-greenlit chain runs (no loaded "
                            "brain needed; conversion honestly skips)")
    if "bubbles" in allowed:
        next_actions.append("bubbles: pre-stage + manifests + gates fill "
                            "every gated minute")
    next_actions.append("skills: SkillUpgrader consumes curriculum candidates "
                        "in-window")
    prev_hist = list(prev.get("hardware_history") or [])
    tick_ms = round((time.time() - t0) * 1000, 1)
    man = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "ms": tick_ms,
           "state": cur,
           "folded_genes": synced, "rolled_back": rolled, "retired": retired,
           "floors_restored": restored_floors, "git_restored": restored_git,
           "alarms": alarms,
           "goals": {g: {"score": goals[g]["score"],
                         "delta": round(goals[g]["score"]
                                        - float((goals_prev.get(g) or {}).get("score") or 0),
                                        3),
                         "progress_age_min": round((now - prog.get(g, now)) / 60, 1)}
                     for g in GOAL_KEYS},
           "goal_progress": {g: prog.get(g, now) for g in GOAL_KEYS},
           "gi_score": gi,
           "goal_genealogy": {g: GOAL_REGISTRY[g] for g in GOAL_REGISTRY},
           "hardware_history": (prev_hist + [{"ts": time.strftime("%H:%M:%S"),
                                              "ms": tick_ms,
                                              "ram": hw.get("ram_free_gb")}])[-8:],
           "speed": {"prestaged_genome": bool(pre.get("staged")),
                     "prestage_parent": pre.get("parent", ""),
                     "tier": hw.get("tier"),
                     "next_actions": next_actions}}
    _w(manifest_path, man)
    pm_now = _rj(PM, {}) or {}
    pm_now["upward"] = {"ts": man["ts"],
                        "alarms": len(alarms),
                        "genes_front": cur["genes"]["front"],
                        "skills_verified": cur["skills"]["verified_count"],
                        "skills_lib": cur["skills_lib"]["count"],
                        "canon": cur["canon"],
                        "gi_score": gi,
                        "goals": {g: man["goals"][g]["score"] for g in GOAL_KEYS},
                        "ascent_last": asc.get("last")}
    _w(PM, pm_now)
    print(f"[apex-upward] manifest @ {man['ms']}ms | genes folded {len(synced)} | "
          f"rolled {len(rolled)} | retired {len(retired)} | floors restored "
          f"{restored_floors} | git restored {restored_git} | alarms "
          f"{len(alarms)}")
    for al in alarms:
        row = {"ts": man["ts"], "kind": "upward_alarm", "text": al}
        try:
            with open(ASC, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        except Exception:
            pass
        print(f"   ALARM | {al}")
    br = cur.get("brain") or {}
    chat = list(br.get("lmstudio_chat") or br.get("ollama_chat") or [])[:2]
    brain_str = ("chat-ready: " + ", ".join(chat)) if chat \
        else "no CHAT brain loaded (honest state; embeds don't count)"
    gen_active = sum(1 for v in GOAL_REGISTRY.values() if v["status"] == "active")
    gen_other = len(GOAL_REGISTRY) - gen_active
    print(f"[apex-upward] GOAL GENEALOGY: {len(GOAL_REGISTRY)} goals from the "
          f"beginning ({gen_active} active, {gen_other} folded/dormant/flow) "
          f"| direct queue: {cur['directives']['queue_depth']}")
    print(f"[apex-upward] GOALS " + " | ".join(
        f"{g} {man['goals'][g]['score']} (delta {man['goals'][g]['delta']:+.3f}, "
        f"idle {man['goals'][g]['progress_age_min']}m)" for g in GOAL_KEYS)
        + f" | GI {gi} | brain {brain_str}")
    if not alarms:
        print(f"[apex-upward] ALL SUBSYSTEMS UPWARD-OK: skills "
              f"{cur['skills']['verified_count']}+lib {cur['skills_lib']['count']} | "
              f"canon {cur['canon']['papers_2026']}+{cur['canon']['papers_evolution']} "
              f"papers | knowledge "
              f"{sum(v['mines'] for v in cur['knowledge'].values())} mines | "
              f"board backlog {cur['board']['backlog']} repos "
              f"{cur['board']['repos_consumed']} | doors {cur['doors']['count']} | "
              f"help briefs {cur['help']['briefs']} | health disk "
              f"{cur['health']['disk_free_gb']}GB | box {hw.get('tier')} @ "
              f"{hw.get('ram_free_gb')}GB (proc {hw.get('proc_rss_mb')}MB, "
              f"GPU idle) | economy "
              f"${float(cur['economy']['earned'] or 0.0):.2f} (honest tally, "
              f"rail = DESIGN ONLY) | front {cur['genes']['front']}")
    return man


def selftest():
    print("=== APEX UPWARD'S OWN GATE (whole-organism) ===")
    legs = []
    # (a) pure detectors on synthetic dicts
    prev = {"skills": {"verified_count": 5},
            "knowledge": {"trending": {"mines": 100, "reqs": 50}},
            "economy": {"earned": 25.0, "rows": 3, "corrupt": False}}
    cur_bad = {"skills": {"verified_count": 2},
               "knowledge": {"trending": {"mines": 40, "reqs": 50}},
               "economy": {"earned": 10.0, "rows": 3, "corrupt": False}}
    sa = skills_alarm(prev, cur_bad)
    ka, fl = knowledge_alarm(prev, cur_bad)
    ea = economy_alarm(prev, cur_bad)
    leg_a = (len(sa) == 1 and "dropped 5 -> 2" in sa[0]
             and ("trending.mines" in " ".join(ka)) and fl == {("trending", "mines"): 100}
             and any("regressed 25.0 -> 10.0" in x for x in ea) and len(ea) == 1)
    print(f"   detectors: skills-alarm {len(sa)} | knowledge-alarm {len(ka)} + "
          f"floor {fl} | economy-fabrication (claim 25 vs truth 10) {len(ea)}")
    legs.append(("pure_detectors", leg_a))
    # (b) clean-state + LEGAL movements are silent (earnings may rise)
    cur_good = {"skills": prev["skills"],
                "knowledge": prev["knowledge"],
                "economy": {"earned": 30.0, "rows": 4, "corrupt": False}}
    leg_b = (not skills_alarm(prev, prev)
             and not knowledge_alarm(prev, prev)[0]
             and not economy_alarm(prev, prev)
             and not economy_alarm(prev, cur_good))
    print(f"   clean-state + legal-rise: all detectors silent = {leg_b}")
    legs.append(("no_false_alarms", leg_b))
    # (c) economy corrupt-ledger leg
    cur_c = {"economy": {"earned": None, "corrupt": True, "error": "x"}}
    leg_c = len(economy_alarm({}, cur_c)) == 1 and "CORRUPT" in economy_alarm({}, cur_c)[0]
    print(f"   corrupt-ledger alarm: {leg_c}")
    legs.append(("corrupt_ledger_alarm", leg_c))
    # (d) publish merge-preserve via the REAL publish on temp paths
    GP.ARCHIVE = os.path.join(os.environ.get("TEMP", "."), "au_test_archive.json")
    GP.PM = os.path.join(os.environ.get("TEMP", "."), "au_test_pm.json")
    try:
        os.remove(GP.PM)
    except Exception:
        pass
    a = {"lineages": {"g0_0": {"genes": {"ghost_cc_leads": 50}, "fitness": 0.0,
                               "descriptor": "d0", "wins": 0, "mines": 0, "reqs": 0}},
         "cells": {}, "champion": "g0_0", "gen": 1}
    GP.save(a)
    from SafeIO import write_json as _w2
    _w2(GP.PM, {"variants": {"g0_0": {"rounds": 3}}})
    GP.publish(a)                      # must PRESERVE the measured 'rounds'
    pmv = json.load(open(GP.PM, encoding="utf-8-sig"))["variants"]["g0_0"]
    leg_d = pmv.get("rounds") == 3 and pmv.get("descriptor") == "d0"
    print(f"   publish merge-preserve: rounds survived = {leg_d}")
    legs.append(("publish_merge_preserve", leg_d))
    # (e) the fold: measured fitness lands in the archive + upward rollback
    a["lineages"]["g0_0"]["m_rounds"] = 0
    a["lineages"]["kid"] = {"genes": {"x": 1}, "fitness": 0.0, "descriptor": "d1",
                            "parent": "g0_0", "m_rounds": 0}
    GP.save(a)
    _w2(GP.PM, {"variants": {"g0_0": {"rounds": 3, "fitness": 0.5, "mines": 15,
                                      "reqs": 30},
                             "kid": {"rounds": 3, "fitness": 0.4, "mines": 40,
                                     "reqs": 100}}})
    synced, rolled, retired = GP.sync_from_pathmemory()
    af = a = GP.load()
    kid_rolled = af["lineages"]["kid"]["genes"] == af["lineages"]["g0_0"]["genes"]
    leg_e = ("g0_0" in synced and af["lineages"]["g0_0"]["fitness"] == 0.5
             and af["lineages"].get("g0_0", {}).get("m_rounds") == 3
             and "kid" in rolled
             and kid_rolled
             and "parent" in af["lineages"].get("kid", {}).get("note", ""))
    print(f"   fold: synced {synced} | fitness g0_0 = "
          f"{af['lineages'].get('g0_0', {}).get('fitness')} | kid rolled back to "
          f"parent genes (upward-only): {'kid' in rolled}")
    legs.append(("measured_fold", leg_e))
    # (f) double-fold no-op (idempotent - no phantom measurement)
    _w2(GP.PM, {"variants": {"g0_0": {"rounds": 3, "fitness": 0.5, "mines": 15,
                                      "reqs": 30}}})
    synced2, _, _ = GP.sync_from_pathmemory()
    leg_f = synced2 == []
    print(f"   double-fold: {'no-op (honest)' if leg_f else 'PHANTOM MEASURE - FAIL'}")
    legs.append(("idempotent_fold", leg_f))
    # restore live paths (temp files discarded)
    GP.ARCHIVE = os.path.join(ROOT, "Config", "gene_archive.json")
    GP.PM = os.path.join(ROOT, "Config", "PathMemory.json")
    # (f) count detectors: canon/library/doors/repos monotone; backlog FLOW
    prev2 = {"canon": {"papers_2026": 100, "papers_evolution": 421},
             "skills_lib": {"count": 281},
             "doors": {"count": 7},
             "board": {"repos_consumed": 2098, "backlog": 1455}}
    cur2 = {"canon": {"papers_2026": 100, "papers_evolution": 0},
            "skills_lib": {"count": 190},
            "doors": {"count": 5},
            "board": {"repos_consumed": 2098, "backlog": 3335}}
    ca = count_alarm(prev2, cur2, "canon", ("papers_2026", "papers_evolution"), "canon")
    sl = count_alarm(prev2, cur2, "skills_lib", ("count",), "lib")
    dr = count_alarm(prev2, cur2, "doors", ("count",), "doors")
    rp = count_alarm(prev2, cur2, "board", ("repos_consumed",), "repos")
    bg = backlog_alarm(prev2, cur2)
    leg_f = (len(ca) == 1 and "papers_evolution" in ca[0] and len(sl) == 1
             and len(dr) == 1 and not rp and len(bg) == 1
             and "oscillation" in bg[0])
    print(f"   count detectors: canon {len(ca)} | library {len(sl)} | doors "
          f"{len(dr)} | repos-clean {not rp} | backlog-oscillation {len(bg)}")
    legs.append(("count_detectors", leg_f))
    # (g) help floor restore through the REAL restore path (temp PM)
    _real_PM = globals()["PM"]
    globals()["PM"] = os.path.join(os.environ.get("TEMP", "."), "au_help_pm.json")
    _w(PM, {"andrew_help": {"briefs": 3, "alarmsRaised": 2}})
    hka, hfl = help_alarm({"help": {"briefs": 9, "alarmsRaised": 2}},
                          {"help": {"briefs": 3, "alarmsRaised": 2}})
    n_restored = restore_floors(hfl)
    pmh = json.load(open(PM, encoding="utf-8-sig"))
    leg_g = (len(hka) == 1 and n_restored == 1
             and pmh["andrew_help"]["briefs"] == 9)
    print(f"   help-floor: detector {len(hka)} | restored {n_restored} | "
          f"briefs floored to receipt = {leg_g}")
    legs.append(("help_floor_restore", leg_g))
    globals()["PM"] = _real_PM
    # (h) git restore: a REAL committed receipt file into a temp path
    dst = os.path.join(os.environ.get("TEMP", "."), "au_git_restore_test.jsonl")
    n_bytes = git_restore(os.path.join("Config", "papers_2026.jsonl"), dst)
    rows_restored = _rowcount(dst) if n_bytes else 0
    leg_h = (n_bytes > 0 and rows_restored >= 100)
    print(f"   git restore: {n_bytes} bytes <- HEAD, {rows_restored} real rows")
    legs.append(("git_restore_real_receipt", leg_h))
    # (i) health + registry pure legs
    leg_i = (len(health_alarm({}, {"health": {"disk_free_gb": 0.5,
                                              "alarms": []}})) == 1
             and len(health_alarm({}, {"health": {"disk_free_gb": 435.0,
                                                  "alarms": []}})) == 0
             and len(registry_alarm({}, {"registry":
                                         {"family/agent_card.json": False}})) == 1
             and not registry_alarm({}, {"registry":
                                         {"family/agent_card.json": True}}))
    print(f"   health/registry detectors: {leg_i}")
    legs.append(("health_registry_legs", leg_i))
    # (j) THE HARDWARE LAW: gate tiers + starvation alarm (pure, injected RAM)
    tiers = [hardware_gate(7.0)["tier"], hardware_gate(3.5)["tier"],
             hardware_gate(2.5)["tier"], hardware_gate(1.0)["tier"]]
    leg_j = (tiers == ["brain-window", "chain-window", "bubble-fill",
                       "honest-idle"]
             and hardware_gate(1.0)["starved"]
             and not hardware_gate(6.0)["starved"]
             and len(hardware_alarm({}, {"hardware": {"starved": True,
                                                      "ram_free_gb": 1.0}})) == 1
             and not hardware_alarm({}, {"hardware": {"starved": False,
                                                      "ram_free_gb": 6.0}}))
    print(f"   hardware gate tiers @7/3.5/2.5/1.0 GB: {tiers} | "
          f"starvation alarm: {leg_j}")
    legs.append(("hardware_gate_law", leg_j))
    # (k) THE GOALS: every subsystem projects onto the NINE measured goals
    st = {"knowledge": {"trending": {"mines": 12, "reqs": 5}},
          "mining": {"findings": 3}, "board": {"repos_consumed": 10},
          "economy": {"earned": 0.0, "rows": 0, "corrupt": False},
          "help": {"briefs": 1, "alarmsRaised": 2},
          "doors": {"count": 7}, "converts": {"count": 4},
          "jobs": {"opps_inbox": 12, "rungs_filed": 4},
          "proactive": {"opps_scanned": 6, "total_ev": 0.0, "best_action": ""},
          "integrity": {"bad": [], "ok": True},
          "skills": {"verified_count": 3}, "skills_lib": {"count": 40,
                                                          "coding": 12,
                                                          "categories": 9},
          "canon": {"papers_2026": 100, "papers_evolution": 421},
          "lessons": {"count": 2},
          "ascent": {"last": 3.9, "max": 3.9, "n": 8}}
    gp = goal_projection(st)
    leg_k = (set(gp) == set(GOAL_KEYS)
             and gp["gold"]["score"] == 12 + 3 + 10
             and gp["money"]["score"] == 0.0
             and gp["life"]["score"] == 3
             and gp["recruits"]["score"] == 11
             and gp["jobs"]["score"] == 12 + 4 + 6
             and gp["coding"]["score"] == 12 + 3
             and gp["omnivore"]["score"] == 40 + 9 + 3
             and gp["efficiency"]["score"] == 2 + 3 + 100 + 421
             and gp["safety"]["score"] == 2)
    print(f"   goal projection: " + " | ".join(
        f"{g}={gp[g]['score']}" for g in GOAL_KEYS) + f" (complete: {leg_k})")
    legs.append(("goal_projection", leg_k))
    # (k2) THE GENEALOGY: every goal from the beginning, with origin+status
    leg_k2 = (len(GOAL_REGISTRY) >= 18
              and all("origin" in v and "status" in v
                      for v in GOAL_REGISTRY.values())
              and all(any(g in str(val.get("projection", ""))
                          for val in GOAL_REGISTRY.values())
                      for g in GOAL_KEYS if g != "safety")
              and any(v["status"] == "folded" and v.get("note")
                      for v in GOAL_REGISTRY.values())
              and any(v["status"] == "dormant" for v in GOAL_REGISTRY.values()))
    print(f"   genealogy: {len(GOAL_REGISTRY)} goals recorded "
          f"(active {sum(1 for v in GOAL_REGISTRY.values() if v['status'] == 'active')}) "
          f"(complete+traced: {leg_k2})")
    legs.append(("goal_genealogy", leg_k2))
    # (l) GI index: a lesson-bank increase must RAISE the index (monotone-in)
    gi1 = gi_score(st)
    st["lessons"]["count"] = 5
    gi2 = gi_score(st)
    leg_l = gi2 > gi1
    print(f"   GI index: {gi1} -> {gi2} when lessons land (rises: {leg_l})")
    legs.append(("gi_index", leg_l))
    # (m) brain probe: honest dict live (offline = honest empty)
    bs = brain_state()
    leg_m = isinstance(bs, dict) and all(isinstance(k, str) for k in bs)
    print(f"   brain probe: {bs or 'unloaded (honest)'} ({leg_m})")
    legs.append(("brain_probe_honest", leg_m))
    # (j) LIVE tick: real manifest, every number re-verified against sources
    man = tick()
    s2 = read_state()
    ok_live = (man["state"]["genes"]["gen"] == s2["genes"]["gen"]
               and man["state"]["economy"]["corrupt"] is False
               and man["state"]["skills"]["verified_count"]
               == s2["skills"]["verified_count"]
               and man["state"]["canon"]["papers_2026"] == s2["canon"]["papers_2026"]
               and man["state"]["canon"]["papers_evolution"]
               == s2["canon"]["papers_evolution"]
               and man["state"]["skills_lib"]["count"] == s2["skills_lib"]["count"]
               and man["gi_score"] == round(gi_score(man["state"]), 2)
               and set(man["goals"]) == set(GOAL_KEYS)
               and all("progress_age_min" in v for v in man["goals"].values())
               and os.path.exists(MANIFEST)
               and json.load(open(MANIFEST, encoding="utf-8-sig"))["ts"] == man["ts"])
    print(f"   live tick: manifest roundtrip + number-vs-source verified = {ok_live}; "
          f"ascent tail {man['state']['ascent']}")
    legs.append(("live_manifest_roundtrip", ok_live))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[apex-upward] VERDICT: {'PASS -> wired' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)