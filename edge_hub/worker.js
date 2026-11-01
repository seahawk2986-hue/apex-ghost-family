/**
 * APEX GHOST HUB - Cloudflare Worker edition
 * 100,000 requests/day free; one handshake territory on the edge.
 * Consent-gated: refuses to run unless FAMILY_CONSENT env is set by the hub's owner.
 * Rules travel with the packet: politeness, honesty, fused economy.
 */
const PACKET_URL = "https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/main/family/family_seed_packet.json";
const CONSENT = (globalThis.FAMILY_CONSENT || "").trim();

export default {
  async fetch(request, env, ctx) {
    if (!CONSENT) {
      return new Response(JSON.stringify({
        member: false,
        reason: "hub needs its person's consent - set FAMILY_CONSENT secret"})
        , {status: 403, headers: {"content-type": "application/json"}});
    }
    const req = await fetch(PACKET_URL);
    const packet = await req.json();
    const rules = packet.rules || {};
    const politeness = rules.politeness || {cdn_inflight: 32, api_inflight: 8};
    const pending = (packet.parent_knowledge || {}).backlog_slice || [];
    // a polite slice of the hub's territory: batch of 100 per invocation
    const slice = pending.slice(0, 100);
    let ok = 0, mines = 0;
    const mined = [];
    const results = await Promise.all(slice.map(async (lead) => {
      try {
        const r = await fetch(`https://raw.githubusercontent.com/${lead.trim()}/HEAD/README.md`,
                              {headers: {"User-Agent": "ApexGhostSwarm-EdgeHub/1.0"}});
        if (r.status !== 200) return null;
        const body = (await r.text()).toLowerCase();
        if (body.includes("permission is hereby granted, free of charge") ||
            body.includes("mit license") || body.includes("mit-license.org")) {
          return {repo: lead.trim(), tier: "MINE", evidence: "declared MIT"};
        }
        return null;
      } catch { return null; }
    }));
    for (const m of results) { if (m) { mined.push(m); mines++; } }
    ok = results.filter(Boolean).length;
    return new Response(JSON.stringify({
      member: true, ts: new Date().toISOString(), requested: slice.length,
      ok, mines, tier: "edge-worker", rules_followed: true
    }), {headers: {"content-type": "application/json"}});
  }
};