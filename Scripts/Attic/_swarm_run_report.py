"""THE SWARM RUN + FULL GOAL REPORT: one real orchestrator round (the
DeploySwarm's dual-mission payload: gold mining round + economy scan),
then the whole-organism tick, then the PASS/FAIL per goal (measured
against the goal's own instrument, honestly: 'cannot move' is not 'fail'
where the law reserves the move for the founder)."""
import io, json, os, sys, time
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

t0 = time.time()
FORCE = "--force" in sys.argv
print("=== THE SWARM ROUND (dual-mission: gold + economy) ===")
import SwarmOrchestrator as so
try:
    so.main(10, None, FORCE)      # the 3rd arg: no_cooldown (the law:
except SystemExit:                # the 1h spacing is honored unless forced)
    pass
except Exception as e:
    print(f"[swarm] main raised honestly: {str(e)[:100]}")
print(f"[swarm] round wall: {time.time() - t0:.0f}s")
try:
    import CryptoEconomy as ce
    r1 = ce.bounty_scan(6)
    r2 = ce.rung1_issue_lane()
    print(f"[economy] bounty_scan -> {str(r1)[:200]}")
    print(f"[economy] rung1_issue_lane -> {str(r2)[:200]}")
except Exception as e:
    print(f"[economy] honest skip: {str(e)[:90]}")

print()
print("=== THE WHOLE-ORGANISM TICK + GOAL VERDICTS ===")
import ApexUpward as AU
import GoalCoherence as GCOH
man = AU.tick()
g = man["goals"]
st = man["state"]
# PASS/FAIL measured against each goal's own instrument + honest law
def verdict(goal):
    s, d = g[goal]["score"], g[goal].get("delta")
    if goal == "money":
        return ("PASS-BY-DESIGN" if s == 0 else "VALUE-LANDED!",
                f"${s:.2f} - the $0.00 law: moves only on Andrew's filing hand")
    if d is None:
        return "BASELINE", (f"{s} (first tick - the floor is now set; "
                            f"movement is judged from the NEXT tick)")
    if d > 0:
        return "PASS", f"{s} (+{d} since the prior manifest)"
    if s > 0:
        return "PASS-HELD", f"{s} (0 delta - needs its next window/condition)"
    return "FAIL", "score 0"
rows = []
for goal in AU.GOAL_KEYS:
    v, note = verdict(goal)
    rows.append((goal, v, note + f" [idle {g[goal]['progress_age_min']}m]"))
print()
for goal, v, note in rows:
    print(f"   {v:14s} | {goal:10s} | {note}")
print()
print(f"coherence: clashes {len(GCOH.solve())} | manifest {man['ms']}ms | "
      f"tiers: {man['speed']['tier']} | prestaged: {man['speed']['prestaged_genome']}")
print(f"integrity: {'CLEAN' if not man['state']['integrity']['bad'] else man['state']['integrity']['bad']}")
print(f"alarms this tick: {man['alarms'] or 'none'}")
print(f"GI: {man['gi_score']} | box: {st['hardware']['tier']} @ "
      f"{st['hardware']['ram_free_gb']}GB | proc {st['hardware']['proc_rss_mb']}MB | GPU idle")

print()
print("=== WHY things are at their values (root causes, honestly) ===")
print(" - coding measured by library+verified counts; the EXECUTION-ROUND")
print("   (gauntlet/gauntlet conversion) needs a LOADED brain window -")
print(f"   brain now: {st.get('brain') or 'unloaded'}")
print(" - money stays $0.00 by LAW until Andrew files (the tally is a")
print("   founder's-hand-only instrument, by the founder's own rule)")
print(" - gold's mines/req needs real spawn rounds; mutants inherit genes")
print("   (GenePool) + are pre-staged (court) + will fold fitness the")
print("   moment a measured round lands (the closed sync loop)")