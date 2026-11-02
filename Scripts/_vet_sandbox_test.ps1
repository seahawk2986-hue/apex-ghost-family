# THE STAGE-2 TEST: VetLineRemote end-to-end in the pinned fixture.
# Real net (2 repos = <=6 API calls, tokenless), throwaway lib, 1CPU/512M,
# no mounts (docker cp), the host = untouched, container rm'd after.
$ErrorActionPreference = 'Stop'
$ROOT = 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed'
$STAGE = "$env:TEMP\vetline_stage_20261101"
if (Test-Path $STAGE) { Remove-Item $STAGE -Recurse -Force }
New-Item -ItemType Directory -Force -Path "$STAGE\Config", "$STAGE\family" | Out-Null
& "$ROOT\apex_venv\Scripts\python.exe" -X utf8 -c "
import json
grain = json.load(open(r'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\family\leads_grain.json', encoding='utf-8-sig'))
cut = {'leads': grain['leads'][:2]}
json.dump(cut, open(r'$STAGE\family\leads_grain.json', 'w'))
json.dump({'skills': [], 'built': ''}, open(r'$STAGE\Config\SkillLibrary.json', 'w'))
json.dump({'points': 0}, open(r'$STAGE\Config\GymRewards.json', 'w'))
print('[stage]: the ', len(cut['leads']), '-lead cut written')"
Copy-Item "$ROOT\Scripts\VetLineRemote.py" "$STAGE\VetLineRemote.py"

docker rm -f apex-vet-test 2>$null | Out-Null
docker create --name apex-vet-test --cpus 1 --memory 512m `
    apex-sandbox:latest sleep 420 | Out-Null
docker cp "$STAGE" apex-vet-test:/wl
docker start apex-vet-test | Out-Null
Start-Sleep -Seconds 2
Write-Host "=== the REAL VetLine inside the pinned fixture ==="
docker exec apex-vet-test python -W ignore /wl/VetLineRemote.py 2>&1
Write-Host ("=== vetter exit: " + $LASTEXITCODE + " ===")
Write-Host "=== the in-container asserts ==="
docker exec apex-vet-test python -c "
import json
lib = json.load(open('/wl/Config/SkillLibrary.json'))
rw = json.load(open('/wl/Config/GymRewards.json'))
rows = lib['skills']
print('[lib rows]:', len(rows), '| [meter pts]:', rw.get('points'))
assert len(rows) >= 1, 'no promote happened'
assert all(r['sha256'] and r['vetby'] == 'hub-runner-v1' for r in rows)
assert rw['points'] == 10 * len(rows)
print('[ASSERTS]: PASS - real fetch + real vet + real register + honest meter')"
Write-Host ("=== asserts exit: " + $LASTEXITCODE + " ===")
docker rm -f apex-vet-test | Out-Null
Write-Host "[container removed]: host untouched"