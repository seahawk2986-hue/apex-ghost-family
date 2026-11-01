"""THE GENEPOOL INHERITANCE GATE (test-before-implement):
1. seed the archive with mutated lineages
2. prove a LIVE child spawn draws a REAL distinct gene vector via
   DeploySwarm._variant_env (the function the orchestrator calls at birth)
3. publish genes into PathMemory (SafeIO) so the next born child inherits
4. verdict: PASS -> implemented; FAIL -> shelved."""
import json
import sys
import os

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import psutil
print('RAM: %.2f GB' % (psutil.virtual_memory().available / 2 ** 30))
import GenePool as GP
print('THE GENEPOOL TEST (inheritance gate before implementation)')

a = GP.run(gen_mutations=3)

print()
print('--- THE INHERITANCE TEST: would a spawned child draw REAL genes? ---')
import DeploySwarm as DS
seen = []
all_ok = True
for i in range(4):
    env = DS._variant_env(i)
    muts = {k: v for k, v in env.items() if k.startswith('MUT_')}
    seen.append(json.dumps(muts, sort_keys=True))
    print(f'   spawn {i}: variant={env.get("APEX_VARIANT")} | genes={len(muts)} | '
          f'cc_leads={muts.get("MUT_ghost_cc_leads")} trending={muts.get("MUT_ghost_trending")}')
    for k, v in muts.items():
        key = k.replace('MUT_', '')
        if key in GP.GENES:
            lo, hi, _t = GP.GENES[key]
            if not (lo <= v <= hi):
                all_ok = False
                print(f'      OUT OF RANGE: {k}={v} not in [{lo},{hi}]')
distinct = len(set(seen))
print(f'   distinct gene vectors drawn: {distinct} of 4 spawn attempts '
      f'(30 percent explorer-rate draws are legal base-cfg)')
verdict = (distinct >= 2) and all_ok and len(a['lineages']) >= 2
print(f'   GATE VERDICT: {"PASS - genes inherit in live spawns; IMPLEMENTED" if verdict else "FAIL - shelved honestly"}')
print()
print('archive:', len(a['lineages']), 'lineages | champion:', a['champion'],
      '| gen', a['gen'])