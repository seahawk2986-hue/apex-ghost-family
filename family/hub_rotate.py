"""Hub rotation: a moving window over a large lead pool, skipping repos mined recently. Pure stdlib, no network."""
import json
import os

DAY = 86400.0


def build_pool(packet_backlog, grain_leads):
    """Ordered unique repos: the packet backlog first, then grain leads best score first. Only 'owner/name' strings."""
    out, seen = [], set()
    rows = [str(x).strip() for x in (packet_backlog or [])]
    g = [r for r in (grain_leads or []) if isinstance(r, dict) and r.get("repo")]
    g.sort(key=lambda r: -float(r.get("score") or 0))
    rows += [str(r["repo"]).strip() for r in g]
    for r in rows:
        k = r.lower()
        if r.count("/") == 1 and k not in seen:
            seen.add(k)
            out.append(r)
    return out


def pick_window(pool, seen, cursor, n, now, ttl_days=14):
    """Walk the pool from cursor, take up to n repos not mined within ttl_days. Returns (picked, new_cursor)."""
    if not pool:
        return [], 0
    picked, i, steps = [], cursor % len(pool), 0
    while len(picked) < n and steps < len(pool):
        r = pool[i]
        t = seen.get(r.lower())
        if t is None or now - float(t) >= ttl_days * DAY:
            picked.append(r)
        i = (i + 1) % len(pool)
        steps += 1
    return picked, i


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=0, sort_keys=True)
    os.replace(tmp, path)


def trim_seen(seen, cap=6000):
    if len(seen) <= cap:
        return seen
    keep = sorted(seen.items(), key=lambda kv: -kv[1])[:cap]
    return dict(keep)
