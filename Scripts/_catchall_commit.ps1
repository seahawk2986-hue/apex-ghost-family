$env:PYTHONIOENCODING = 'utf-8'
Set-Location 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed'
Write-Host '--- the uncommitted state:'
git status --short | Select-Object -First 40
git add -A Scripts
git add -u
git commit -m 'THE DAY S FULL INSTRUMENT-COMMIT: the earning-pipeline s entire organ-set (PatchLoop v2-v4 + MuseProvider/Bundle/TestUpgrade + StrictCorrection + SchemaRescue + DreamLand + DreamSchemaPr + GosturdyPr + I18nBuild + ClaimCheck + FounderOneClick + QualityGate + PrWatch + CloudBrain v2 + AgentRoster + BountyLens + GrowthTopics + LandingPage + the honest probes) - every organ committed with its receipts; the free-only roster + the drain-protected ledger standing' 2>&1 | Select-Object -First 1
git pull --rebase --autostash origin main 2>&1 | Select-Object -Last 1
git push 2>&1 | Select-Object -Last 1
git log --oneline -1
Write-Host '--- the delayed site re-verify (the build s 100s):'
& 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\apex_venv\Scripts\python.exe' '-c' "
import time, urllib.request, json, subprocess, sys
time.sleep(100)
try:
    r = urllib.request.urlopen('https://seahawk2986-hue.github.io/apex-ghost-family/', timeout=30)
    body = r.read().decode('utf-8', 'replace')
    print('THE SITE LIVE: HTTP', r.status, '|', len(body), 'bytes | shop-links:', body.count('buy.polar.sh'))
except Exception as e:
    status = getattr(getattr(e, 'fp', None), 'code', 0)
    print('the site not yet:', status or str(e)[:60])
try:
    r3 = urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/seahawk2986-hue/apex-ghost-family/pages/builds/latest',
        headers={'Authorization': 'Bearer ' + open(r'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env'.replace('\\\\', chr(92)) and os.environ.get('GH', '')) if False else {}}), timeout=5) if False else None
except Exception:
    pass
" 2>&1