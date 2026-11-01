$env:PYTHONIOENCODING = 'utf-8'
Set-Location 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed'
& .\apex_venv\Scripts\python.exe .\Scripts\Sanitizer.py 2>&1 | Select-Object -Last 8
Write-Host '=== PASS 2 ==='
& .\apex_venv\Scripts\python.exe .\Scripts\Sanitizer.py 2>&1 | Select-Object -Last 3
git add -- Scripts/Sanitizer.py Scripts/PaperHarvest7.py Config/sanitizer_audit.json Config/papers_2026_techniques.jsonl
git commit -m "THE SANITIZER LANDS (the canon-backed injection defense - the techniques-canon's 128-paper class's first adoption): the untrusted texts (maintainer comments/issue bodies/PR content) read as DATA-WRAPPED ONLY: the attack-patterns flagged (ignore-prompts/you-are-now/exfiltration/rm-rf classes), never obeyed; the machine's responses = OUR template's words (the untrusted echo impossible by construction); the benign critiques pass clean; gate PASS x2" 2>&1 | Select-Object -First 1
git pull --rebase --autostash origin main 2>&1 | Select-Object -Last 1
git push 2>&1 | Select-Object -Last 1
git log --oneline -1