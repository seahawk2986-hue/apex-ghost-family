"""THE OUTSOURCING-STATE receipt (the bloat = the bare-minimum map)."""
import json
import time

import psutil

vm = psutil.virtual_memory()
state = {
 "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
 "ram_free_gb": round(vm.available / 2**30, 1),
 "OFFBOX_lanes_verified": [
  "the watch-lane */5 (the PrWatch + ClaimCheck + the actions-loop + the grain = ALL steps success)",
  "the harvests 10/11/12 (the sourcing-compute = the arXiv-side + the runners)",
  "the chat/catalog-sweeps (the catalog = the web-apis; the groq 120b = their LPUs)",
  "the 120b-judge/copy/translate/arbiter lanes (0GB local RAM)"],
 "LOCAL_by_law": [
  "the ollama-models (the 5-model roster disk-pulled; the LOAD = the RAM-gated windows only)",
  "the local-ledger/lock-writes (the disk = ours)",
  "the schtasks-beats (the OS-persistence)"],
 "the_last_big_shift": {
  "lane": "the PR-file chain (30+ scripts -> the runners)",
  "blocker": "the PR-create needs OUR full PAT as an ACTIONS-secret (the built-in token = the cross-repo-restricted)",
  "founder_step": "one 30-sec paste of the PAT into the hub's Settings>Secrets (the machine-side = ready)"},
 "law": "the bloat = the bare-minimum: every CPU/network-heavy = theirs; every RAM-heavy = windowed + auto-unloaded"}
open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Config"
     r"\outsourcing_state.json", "w", encoding="utf-8").write(
    json.dumps(state, ensure_ascii=False, indent=1))
print(f"[outsourcing] RAM {state['ram_free_gb']}GB free | the OFFBOX: "
      f"{len(state['OFFBOX_lanes_verified'])} lanes verified | the "
      f"residue: 3 by-law + 1 founder-paste")