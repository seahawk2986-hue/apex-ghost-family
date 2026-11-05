"""CloudRegistry - THE INDEFINITENESS GOVERNOR.

Law: 'nothing load-bears on one provider'. This organ keeps the fleet's
verified cloud census honest and durable:

  - every source listed carries its last-verified receipt, $0 status,
    and a LONGEVITY class (our honest estimate, not a promise)
  - nightly probe: cheap health checks; a source that changes
    (closes/starts charging/limits shift) earns a CHANGED receipt and
    the fleet's architecture already routes around it (rotation holds)
  - THE TRULY INDEFINITE tier: the LOCAL layer (ollama + lmstudio +
    downloaded weights + local caches). Hardware we own cannot be
    revoked by any company. The registry names it first, always.
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REG_FILE = os.path.join(ROOT, "Config", "cloud_sources.json")

SOURCES = [
    {"id": "local-ollama", "tier": "local-indefinite",
     "probe": "http://127.0.0.1:11434/api/tags",
     "$0": True, "note": "hardware-owned; cannot be revoked by any company"},
    {"id": "local-lmstudio", "tier": "local-indefinite",
     "probe": "http://127.0.0.1:1234/v1/models",
     "$0": True, "note": "hardware-owned; probes-yet-unverified engines exist (30B)"},
    {"id": "huggingface-datasets-server", "tier": "public-institutional",
     "probe": "https://datasets-server.huggingface.co/rows?dataset="
              "princeton-nlp/SWE-bench_Lite&config=default&split=test"
              "&offset=0&length=1",
     "$0": True, "note": "verified 2026-11-04: 300 SWE-bench instances, no auth"},
    {"id": "github-actions", "tier": "public-institutional",
     "probe": "https://api.github.com/repos/seahawk2986-hue/apex-ghost-family"
              "/actions/runs?per_page=1",
     "$0": True, "note": "free compute for public repos; 3 green receipts tonight"},
    {"id": "github-models", "tier": "incumbent-bundled",
     "probe": None,  # probe needs token HTTP 200 (verified 2026-11-04)
     "$0": True, "note": "inference-plane verified live; rate-capped free tier"},
    {"id": "nim-nvidia", "tier": "vendor-free-tier",
     "probe": "https://integrate.api.nvidia.com/v1/models",
     "$0": True, "note": "500/day observed; key-ring gated"},
    {"id": "openrouter-free", "tier": "community-subsidized",
     "probe": None, "$0": True,
     "note": "per-model daily caps; rightly paranoid: subsidy could end"},
]


def _probe(url, timeout=10):
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status
    except Exception as e:
        code = getattr(e, "code", None)
        return code if code else f"ERR:{str(e)[:60]}"


def main():
    try:
        reg = json.load(open(REG_FILE, encoding="utf-8"))
    except Exception:
        reg = {"sources": {}}
    srcs = reg.setdefault("sources", {})
    for s in SOURCES:
        key = s["id"]
        old = srcs.get(key, {})
        status = _probe(s["probe"])
        row = {"tier": s["tier"], "$0": s["$0"], "note": s["note"],
               "probe": s["probe"], "last_checked": time.strftime(
                   "%Y-%m-%d %H:%M:%S"),
               "probe_status": status if status is not None else "not-probed(key-only)",
               "first_verified": old.get("first_verified") or
                                 (time.strftime("%Y-%m-%d") if status in
                                  (200, None) else None)}
        # THE CHANGED receipt: a source's tier/status shift is fleet news
        if old and old.get("last_checked") and \
                str(old.get("probe_status")) != str(row["probe_status"]) and \
                old.get("probe_status") not in (None, "not-probed(key-only)") and \
                row["probe_status"] != "not-probed(key-only)":
            row["changed"] = {"was": old.get("probe_status"),
                              "now": row["probe_status"]}
        srcs[key] = row
    reg["checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
    reg["policy"] = ("local-first indefinite base; N independent clouds; "
                     "every closure = CHANGED receipt + graceful handoff, "
                     "the floor holds, nothing paid is substituted")
    tmp = REG_FILE + ".tmp"
    os.makedirs(os.path.dirname(REG_FILE), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1)
    os.replace(tmp, REG_FILE)
    for k, v in srcs.items():
        print(f"{k:32s} tier={v['tier']:20s} status={v['probe_status']}"
              f"{(' [CHANGED]' if v.get('changed') else '')}")


if __name__ == "__main__":
    main()
