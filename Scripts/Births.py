"""The family's birth registry - every child counted, every death recorded."""
import json
import os
import time

BIRTHS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "Config", "family_births.jsonl")


def birth(shard, variant, territory, pid):
    _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "birth",
             "child_pid": pid, "shard": shard, "variant": variant,
             "territory": territory})


def death(shard, variant):
    _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "dissolved",
             "child_pid": None, "shard": shard, "variant": variant})


def census():
    try:
        rows = [json.loads(x) for x in open(BIRTHS, encoding="utf-8-sig") if x.strip()]
        b = sum(1 for x in rows if x["event"] == "birth")
        d = sum(1 for x in rows if x["event"] == "dissolved")
        return {"born_total": b, "dissolved_total": d, "alive_now": b - d}
    except Exception:
        return {"born_total": 0, "dissolved_total": 0, "alive_now": 0}


def _append(row):
    try:
        with open(BIRTHS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass
