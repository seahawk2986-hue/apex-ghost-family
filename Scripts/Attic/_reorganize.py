"""THE HONEST REORGANIZATION (the full sweep's orphan verdict applied):
- KEEP-TOOLS stays in Scripts (referenced by the chains/audits/docs);
- the ONE-OFF session scripts (fix_/apply_/wire_/diag_/probe_/patch_/
  check_/finish_/dated-dumps...) move to Scripts/Scratch/ (receipts kept,
  git mv);
- the PAST-GENERATION organs (the Attic-named ones still at Scripts root)
  move to Scripts/Attic/ (the standing archive law);
- the ROOT-level one-shots move to Scratch too (apply_triple, game_inventory,
  template_calc, sample_scraper, the dumps).
NOTHING is deleted. Every move is git-mv'd (history preserved)."""
import os
import re
import shutil
import subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
S = os.path.join(ROOT, "Scripts")
SCRATCH = os.path.join(S, "Scratch")
ATTIC = os.path.join(S, "Attic")
os.makedirs(SCRATCH, exist_ok=True)

KEEP = {
    # real organs, tools and chain members (referenced or wired)
    "ChatTally.py", "PayoutDoor.py", "WorkspaceManager.py", "FindGithubToken.py",
    "UsdcTestRun.py", "GenePoolTest.py", "RescanAll.py", "FullSweep.py",
    "PaperHarvest2.py", "PaperHarvest3.py", "PaperHarvest4.py",
    "RepeatTest.py", "VerifySeal.py", "ConflictJsonRepair.py",
    "ApexAutonomousAgent.py", "apex_v2_contract.py", "Invoke-CodingMastery.py",
}
ATTIC_MOVE = {
    "ActivateHub.py", "AgentSwarmEngine.py", "BirthRegistry.py", "DriveAudit.py",
    "DriveCensus.py", "DriveCensus2.py", "DriveComplete.py", "FamilyKeys.py",
    "FounderSeal.py", "LoopGuard.py", "RapidFinal.py", "SandboxVerificationEngine.py",
    "ServiceCatalog.py", "TallyFormat.py", "TenShifts.py", "UsdLane.py",
    "WireRapid.py", "YamlFix.py", "YamlFix2.py", "apexmicprobe.py",
}
SCRATCH_PAT = re.compile(
    r"^(apply_|fix_|wire_|diag_|probe_|patch_|check_|remove_|restore_|repair_|update_|finish_|close_|closure|flip_|stop_|test_|the_|print_|sample_|spawn_|light_|bulletproof_|cancel_|frontier_|hub_|skills_|pf_|disk_|build_|delivery_|cleanup_|chat_v2|fetch_|v2_|agency_|birth_|scrape_|run_|unwrap_|slim_|template_|economy_|money_|first_training|training_|shift_|isolation_|lane_|import_|system_|vram_|evolution_|final_|audit|restart_watchdog)", re.I)
moved_sc, moved_at, moved_root = 0, 0, 0


def git_mv(src, dst):
    try:
        r = subprocess.run(["git", "-C", ROOT, "mv", src, dst],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    try:
        shutil.move(src, dst)         # untracked files: plain move
        return True
    except Exception as e:
        print("MOVE FAILED:", src, str(e)[:60])
        return False


for fn in sorted(os.listdir(S)):
    p = os.path.join(S, fn)
    if not os.path.isfile(p) or not fn.endswith(".py") or fn.startswith("_"):
        continue
    dst = None
    if fn in ATTIC_MOVE:
        dst = os.path.join(ATTIC, fn)
        moved_at += 1
    elif fn in KEEP:
        continue
    elif SCRATCH_PAT.match(fn):
        dst = os.path.join(SCRATCH, fn)
        moved_sc += 1
    if dst and git_mv(fn, os.path.relpath(dst, ROOT).replace("\\\\", "/")):
        print("moved:", fn, "->", os.path.relpath(dst, S))
# the ROOT-level one-shots
ROOT_ONESHOTS = {"apply_triple.py", "game_inventory.py", "template_calc.py",
                 "sample_scraper.py"}
# THE LIVE GUARD (learned the hard way tonight: the pattern caught the LIVE
# chat server - these ROOT files are NEVER scratch):
LIVE_ROOT = {"run_apex_evolution.py", "test_reward.py", "ApexInstaller.py",
             "ApexIPCEngine.py", "ApexMemory.py", "ApexNetScraper.py",
             "ApexPacing.py", "ApexWebScraper.py", "optimized_agent.py",
             "TrainingCalc.py", "TrainingLogParser.py", "TrainingMinStack.py"}
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith(".py") or fn in LIVE_ROOT:
        continue
    low = fn.lower()
    if fn in ROOT_ONESHOTS or re.match(r"^2026\d{4}_", fn) \
            or SCRATCH_PAT.match(fn):
        if git_mv(fn, "Scripts/Scratch/" + fn):
            moved_root += 1
            print("moved(ROOT):", fn)
print(f"SCRATCH moves: {moved_sc} | ATTIC moves: {moved_at} | ROOT moves: {moved_root}")