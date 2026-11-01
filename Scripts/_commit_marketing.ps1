$env:PYTHONIOENCODING = 'utf-8'
Set-Location 'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed'
git add -u
git add -- Scripts/MarketingKit.py Scripts/BountyLens.py Scripts/_runner_portable_test.py Config/marketing_kit.json Config/papers_2026_usdmaking.jsonl
if (git status --short) {
  git commit -m 'THE MARKETING KITS READY (the honest quality bar enforced on our OWN drafts): the hype-v1 caught - the honest-specific v2 hand-written (the Show-HN: the real facts, the two PRs, the ask for critique; the Reddit: the etiquette-question format; the X/LinkedIn: the specifics+the ledger); the paste-ready kit lives in Adapter/marketing_kit/ + the hub copy - the founder s identities post them (the machine holds no social identities - the honest limit); harvest9 marketing-canon running (100 docs) + the usdmaking 17 landed; the canon total: 1,116+ papers sourcing the growth'
  git pull --rebase --autostash origin main 2>&1 | Select-Object -Last 1
  git push 2>&1 | Select-Object -Last 1
}
git log --oneline -1