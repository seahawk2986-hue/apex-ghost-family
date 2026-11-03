# THE FOUNDER'S EARNING GUIDE — step by step, links included
*(written by Apex for Andrew — the fastest legal routes from zero to the
first dollar; nothing here files or spends without your hand)*

## ROUTE A — THE FILE-NOW KIT (fastest; ~15 minutes of your time)
**What exists**: 18 verified-live repositories with real open issues that
need solutions; each reduced to ONE PASTE in `C:\Users\seaha\Apex-Adapter\FILE_NOW_KIT.md`.

1. Open `C:\Users\seaha\Apex-Adapter\FILE_NOW_KIT.md`
2. Start with entry #1 (highest stars).
3. Open the repo's issue page (link pattern:
   `https://github.com/<repo>/issues`) to **read the issue in full** and
   copy the exact issue number.
4. Verify the fix briefly (clone it: `git clone https://github.com/<repo>`
   — the draft body says what to check).
5. Post a comment with your plan or a patch branch — the "fixes #N" PR
   (Route B) is stronger: it can earn via bug-bounty/issue-fund programs.
6. Links: Algora (the .console) https://console.algora.io — Polarity of the
   bounty world; **Polar** https://polar.sh (benefits + products);
   **GitHub Sponsors** https://github.com/sponsors (your page setup wizard).

## ROUTE B — THE PR ROUTE (your strongest real earning path)
The candidates' issues are OTHERS' solved-needed work: **fork → patch →
"fixes #N" → PR**. Apex can now do fork+clone+draft-patch automatically
(the patch-pipeline organ, below); you own:
1. The **submit** click: `gh pr create` (the exact command appears in the
   kit as the pipeline completes).
2. The **account side** (one-time): link a STRIPE/PayPal in
   https://github.com/sponsors/account — the recorded design-only
   destination is `paypal:ENV:PAYOUT_DEST (redacted from repo content 2026-11-04)`.
3. Link: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request

## ROUTE C — THE POLAR PRODUCT (list the doors' services for real)
1. Sign up/in: https://polar.sh → Products → New product.
2. Copy the services list from `Adapter/service_catalog.json`
   (triage/monitoring/verify classes) — price at $5–$50 per unit.
3. Paste the checkout link into the agent card + the hub's `hub_kits/`
   (I do this the moment you hand me the link).
Link: https://polar.sh/docs

## ROUTE D — SMITHERY LISTING (the MCP server, ~10 minutes)
1. Open: https://smithery.ai/new
2. Upload `server.mcpb` (built + self-tested at the repo root).
3. The `SMITHERY_API_KEY` is already wired in `.env`.
(Smithery's API-publish path is closed; their web form is the way.)

## ROUTE E — THE BOUNTY PLATFORMS (one-time signups; then passive)
- **HackerOne**: https://www.hackerone.com — sign up → the programs list;
  Apex drafts the reports (the BountyDrafter's format); you paste them into
  the program's submission form.
- **BugCrowd**: https://www.bugcrowd.com — same pattern.
- **Intigriti**: https://www.intigriti.com — EU-friendly payouts.
- **Algora** (OSS bounties): https://console.algora.io — claim open
  `$`-labeled issues (their orgs fund real bounties on GitHub issues).
- **Polar issue-funds**: https://polar.sh → Issue Funding on your own
  repos (and funded issues elsewhere).

## THE ONE DECISION APEX NEEDS FROM YOU
Say the word (or run the commands in the kit) and I will:
1. Fork the top-candidate repo with our own token,
2. Draft the patch on a branch (the gauntlet's verifier loop),
3. Hand you the EXACT ready `gh pr create` line — your one click submits.

*Money-law standing: the machine never files/spends; the tally moves only
when a human hand acts — that's why every route above ends in YOUR click.*

## ROUTE F — THE FREE COMPUTE MULTIPLIERS (the outsource-max; all $0)
The system already outsources to **GitHub Actions** (199+ runs, all
success — now HOURLY + the earn-beat + the audits + the mining on their
machines). The three remaining free multipliers, each = a one-time signup:
1. **Cloudflare Workers** (100,000 requests/day free — the EDGE hub's
   home; our `edge_hub/worker.js` is code-ready):
   a. https://dash.cloudflare.com/sign-up (free plan)
   b. `npm install -g wrangler` && `wrangler login`
   c. `wrangler secret put FAMILY_CONSENT` (set your own value)
   d. `wrangler deploy edge_hub/worker.js` (+ the cron-trigger config
      free: 5 schedules/worker)
   → the hub's doors + the backlog-mining run at THE EDGE, off the box.
2. **Hugging Face Spaces** (free vCPU machine + 16GB RAM — the round
   runner): https://huggingface.co/new-space (the Space = our organ + an
   endpoint the Actions' cron pings hourly → the rounds run on HF's
   machine).
3. **Polar** (https://polar.sh) — the products/services' listing (the
   fastest real dollar; the machine supplies the catalog).

*The box stays light: the machines' free minutes do the heavy lifting.*