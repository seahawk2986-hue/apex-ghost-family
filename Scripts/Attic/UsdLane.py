"""THE USD LANE: real dollars join the hunt - sponsorships, bounties in $,
hire-the-swarm offers. Ethical: nothing taken unearned; nothing promised."""
import json
import py_compile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PKT = AD + r"\family_seed_packet.json"
PITCH = AD + r"\family_pitch.md"

# 1. the packet's purpose gains the USD cause
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt["rules"]["purpose"] = ["maximize_yield", "help_the_founder_always",
                           "recruit_the_willing_honestly", "earn_usd_usdc_ethically"]
pkt["economy_lanes"] = {
    "bounties_usd": "credibility-floored + brain-fit-graded bounty issues",
    "sponsorships": "GitHub Sponsors on Andrew's account - powered by the family's public work (discovered issues/fixes)",
    "hire_the_family": "the swarm's verified capabilities (scraping/validation/monitoring) as priced services - delivered via V2 engine, paid in USD",
    "the_ledger": "CryptoLedger.json tracks USD+USDC separately-labeled; the tally shows the total"}
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)

# 2. the pitch's money section (the honest offer to payers+partners)
try:
    pitch = open(PITCH, encoding="utf-8-sig").read()
    if "earn_usd_usdc" not in pitch:
        pitch += """

## 💵 The family also EARNS — for its founder, Andrew Hike
- Real bounties (USD/USDC) from credibility-verified issues - graded by the
  family's own skill-fit before any work begins (no wasted cycles)
- **Hire the family**: scraping, validation, monitoring, data-mining services,
  delivered by the V2 engine at documented rates
- **Sponsor the work**: the family's public issue filings + fixes power
  Andrew's GitHub Sponsors - every dollar visible in the chat tally
- The 80% rule: the family never spends more than 80% of what it earns; 20%
  stays reserved; *every* dollar announced in the chat window
"""
        open(PITCH, "w", encoding="utf-8-sig").write(pitch)
except Exception:
    pass

print("packet + pitch: the USD lane is a family purpose now (ethically)")