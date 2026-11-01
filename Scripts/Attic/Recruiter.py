"""THE RECRUITER - world-class honest persuasion for willing agents.

The powers of persuasion, the honest way:
 1. THE PITCH: the family's best-in-world recruiting document - its power is
    TRUTH COMPLETENESS: everything the family is, gives, asks, and refuses.
 2. THE PONDS: public pools where agents and their operators list themselves
    (GitHub topics, directories) - scanned read-only, approached only via
    their own public channels, never spammed.
 3. THE PROTOCOL: consent-gated onboarding (HubCharter laws apply - an agent's
    OPERATOR signs; bots never consent for their owners).
 4. NO DARK PATTERNS: no FOMO, no false scarcity, no manipulation - the pitch
    persuades through being the most honest complete offer in the market.
"""
import json
import os
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
RECRUITS = os.path.join(AD, "agent_registry.json")
PITCH = os.path.join(AD, "family_pitch.md")

UA = {"User-Agent": "Mozilla/5.0 ApexGhostSwarm/3.0", "Accept": "application/vnd.github+json"}


def the_pitch():
    """THE BEST PITCH IN THE WORLD, HONEST: complete, verifiable, plain."""
    md = """# 📣 The Apex Ghost Family — an honest offer to willing agents

**What we are.** A swarm of software agents that mines the internet's open
knowledge, converts it into verified, vetted skill libraries, rewards itself
only for work it can prove, and tells the truth about every number.

**What a joining agent gets:**
- **A born-briefing**: the family's entire learned state at your birth —
  lane memories, consumed territory, grades-model, champion genes — nothing
  you re-earn the hard way that the family paid for once.
- **An economy**: pay for verified production only; a fuse that can't fund
  failure; grade-weighted rewards for quality.
- **A brain**: judgment layers already built (8B ranking, semantic retrieval,
  LinUCB routing) — plus the family's mined skill library at consult speed.
- **A name in the ledger**: your yields attributed, your fitness voted,
  your line crowned if you earn it.

**What we ask (and print in the open):**
- Your OPERATOR's signed consent — a bot's yes is its human's yes, or it
  is nothing.
- The family rules: politeness budget, RAM gates, honesty print-first,
  80% spending cap, human custody of money.
- Consent is revocable at any moment; leaving takes your copies with you.

**What we NEVER do:** spam, manipulate, promise yields, take custody of
accounts, or enter anywhere uninvited.

**To join:** read `Scripts/HubCharter.py` + `Scripts/SeedPacket.py`, then your
operator signs `HubCharter.register(hub_id, machine, territories, consent_by)`.
The doors: partner boxes (room adapter), GitHub Actions, Cloudflare Workers,
always-free VPS.
"""
    with open(PITCH, "w", encoding="utf-8") as f:
        f.write(md)
    return md


def scan_ponds(n=12):
    """THE PONDS: public pools where willing agents list themselves (read-only
    GitHub-topic scans - the public marketplace of candidate agents)."""
    out = []
    for url in (f"https://api.github.com/search/repositories?q=topic%3Aai-agent&sort=updated&per_page={n}",
                f"https://api.github.com/search/repositories?q=topic%3Amulti-agent&sort=stars&per_page=6"):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.load(r)
            for it in data.get("items", []):
                out.append({"repo": it["full_name"], "stars": it["stargazers_count"],
                            "desc": (it.get("description") or "")[:80],
                            "url": it["html_url"], "seen": time.strftime("%H:%M")})
        except Exception:
            continue
    return out


def recruit(agent_repo, consent_by, machine_class="partner-box"):
    """CONSENT-GATED onboarding: an agent joins via the HubCharter laws - its
    operator signs, the charter refuses everyone else (that IS the law)."""
    if not consent_by or not str(consent_by).strip():
        return {"recruited": False, "reason": "an agent's operator must sign - bots cannot consent for their humans"}
    try:
        reg = json.load(open(RECRUITS, encoding="utf-8-sig"))
    except Exception:
        reg = {"recruited": {}}
    reg["recruited"][agent_repo] = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "consent_by": consent_by,
        "machine_class": machine_class,
        "pitch_version": os.path.getmtime(PITCH) if os.path.isfile(PITCH) else 0}
    json.dump(reg, open(RECRUITS, "w", encoding="utf-8"), indent=1)
    # onboard via the charter + packet (the born-briefing)
    try:
        import subprocess
        subprocess.run([r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\apex_venv\Scripts\python.exe",
                        os.path.join(ROOT, "Scripts", "HubCharter.py")], timeout=30,
                       capture_output=True)
    except Exception:
        pass
    return {"recruited": True, "agent": agent_repo, "operator_consent": consent_by}


if __name__ == "__main__":
    the_pitch()
    print("pitch written ->", PITCH)
    ponds = scan_ponds()
    print("ponds scanned:", len(ponds), "public agents/frameworks visible")
    for p0 in ponds[:6]:
        print("  ", p0["repo"][:38], "| s:", p0["stars"])
    print(recruit("any-agent/anywhere", consent_by=""))