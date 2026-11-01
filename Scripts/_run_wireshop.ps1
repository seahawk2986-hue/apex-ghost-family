$env:PYTHONIOENCODING = 'utf-8'
Set-Location 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed'
& .\apex_venv\Scripts\python.exe .\Scripts\WireShop.py 2>&1
git add -u
git add -- Config/polar_shop.json Config/CostLedger.json Scripts/PolarAgent.py Config/earn_lane_matrix.json
git commit -m 'THE SHOP IS LIVE - 3 real checkout links (the API-created: the Triage-pack 75 / the Code Fix 150 / the Pipeline 200) + the buy-side WIRED: the agent-card buy-field + the service-catalog checkout_url + the doors + the hub README - the payments flow: buyer then Polar then the founder payout; the receipt: SHOP-LIVE in the ledger' 2>&1 | Select-Object -First 1
git pull --rebase --autostash origin main 2>&1 | Select-Object -Last 1
git push 2>&1 | Select-Object -Last 1
git log --oneline -1