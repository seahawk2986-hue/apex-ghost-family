"""FreeDoorWatch - the organ that waits at the free doors.

Rescans OpenRouter's :free pool; diffs against the last-seen list; prints
and commits any NEW free door (a gpt-5:free promo would land here the hour
it appeared). Runs on a GitHub Actions cron (outsourced, $0) or locally.
State: freedor_state.json (last seen ids). $0, keyless for the scan itself.
"""
import io
import json
import os
import pathlib
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
STATE = pathlib.Path(__file__).parent / "freedor_state.json"


def scan():
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models",
                                timeout=30) as r:
        models = json.loads(r.read())["data"]
    free = sorted(m["id"] for m in models if ":free" in m["id"])
    g5 = sorted(m["id"] for m in models
                if "gpt-5" in m["id"].lower() and ":free" in m["id"])
    return free, g5


def main():
    free, g5 = scan()
    seen = set()
    if STATE.exists():
        try:
            seen = set(json.loads(STATE.read_text(encoding="utf-8")))
        except Exception:
            seen = set()
    fresh = sorted(set(free) - seen)
    print("[free doors]:", len(free), "| fresh today:", len(fresh))
    for i in fresh:
        print("   [NEW]:", i)
    for i in g5:
        print("   [GPT-5 FREE DOOR SPOTTED]:", i)
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models",
                                timeout=30) as r:
        models = json.loads(r.read())["data"]
    for fam in ("claude", "grok", "qwen", "deepseek"):
        for m in models:
            if fam in m["id"].lower() and ":free" in m["id"]:
                print(f"   [{fam.upper()} FREE DOOR SPOTTED]:", m["id"])
    STATE.write_text(json.dumps(free, indent=1), encoding="utf-8")
    print("[state updated]:", STATE.name)
    with (pathlib.Path(__file__).parent / "freedoors_NOW.txt").open(
            "w", encoding="utf-8") as f:
        f.write("\n".join(free) + "\n")


if __name__ == "__main__":
    main()