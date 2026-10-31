# hub_kits/README.md — The Four Doors
Every hub lives only with consent. Each kit is staged; the person holds the key.

## Door 1 — LAN partner (Mica's box + room members)
The room adapter (token-authed :8788) is the transport; the partner runs the
room client and grants the hub a territory:
    python Scripts\\SeedPacket.py        # packet written to Apex-Adapter
    (partner pulls it + runs their own ShardWorker; consent logged in HubCharter)

## Door 2 — GitHub Actions (2,000 free minutes/month)
    git init + commit this repo (family/seed packet + .github/workflows/apex-hub.yml)
    add family/CONSENT.txt (your signed consent, dated)
    push → the cron runs every 2h; harvests return as artifacts + pushes

## Door 3 — Cloudflare Workers (100k requests/day)
    cd edge_hub; npx wrangler deploy; wrangler secret put FAMILY_CONSENT
    (consent-gated in the worker's own code — 403 without it)

## Door 4 — Always-free VPS (Oracle-class)
    curl the seed packet; python Scripts\\DeploySwarm.py on the box; cron it
    (the rules ride in the packet; GrainLine pushes home manifest-verified)

## The family laws (they travel with every packet)
1. Politeness budget is global and rides in the packet
2. RAM gates + honesty print-or-didnt-happen
3. Evolution: measured fitness only; eviction ratchet; champion 2% rule
4. Economy: pay only verified growth; 80% spending cap; custody human-only
5. Consent: no hub, no member, no host without its person's yes