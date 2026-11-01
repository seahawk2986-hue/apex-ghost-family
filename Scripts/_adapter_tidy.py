"""THE ADAPTER'S HONEST TIDY-UP: the 94 one-shot session scripts (apply_*/
fix_*/wire_*/diag_*/probe_*/patch_*/check_*/repair_*...) move to
Adapter\Scratch\ (receipts preserved, NOTHING deleted) - the full sweep's
orphan verdict applied where the one-shots actually live. The adapter's
LIVE machinery (the job engine, the state/board/ledger files, heartbeats,
doors) stays untouched."""
import os
import re
import shutil

AD = r"C:\Users\seaha\Apex-Adapter"
SCRATCH = os.path.join(AD, "Scratch")
os.makedirs(SCRATCH, exist_ok=True)
PAT = re.compile(
    r"^(apply_|fix_|wire_|diag_|probe_|patch_|check_|remove_|restore_|repair_|update_|finish_|close_|flip_|stop_|test_|the_|print_|sample_|spawn_|light_|bulletproof_|cancel_|frontier_|hub_|skills_|pf_|disk_|build_|delivery_|closure|cleanup_|chat_v2|fetch_|v2_|agency_|apex_v2|birth_|scrape_|run_|unwrap_|slim_|template_|economy_|money_|first_training|training_|shift_|isolation_|lane_|import_|system_|vram_|evolution_|final_|restart_watchdog|audit|game_inv)", re.I)
LIVE_GUARD = {"v2_job_engine.py", "v2_job_engine_FINAL_audit.py",
              "wire_heavy_rewards.py", "player_scan.py"}
moved, kept = 0, 0
for fn in sorted(os.listdir(AD)):
    p = os.path.join(AD, fn)
    if not os.path.isfile(p) or not fn.endswith((".py", ".pyw")):
        continue
    if fn in LIVE_GUARD or fn.startswith("_"):
        kept += 1
        continue
    if PAT.match(fn):
        try:
            shutil.move(p, os.path.join(SCRATCH, fn))
            moved += 1
        except Exception as e:
            print("FAILED:", fn, str(e)[:50])
    else:
        kept += 1
print(f"moved {moved} one-shots -> Adapter\\Scratch; kept {kept} live/tool files")
for fn in sorted(os.listdir(AD))[:14]:
    print("  adapter root now:", fn[:60])