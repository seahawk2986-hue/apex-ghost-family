"""SeekGrowth - Apex's curiosity drive: actively farm openly-published knowledge.

Boundaries written into his desire:
  - public/open sources only, permissive licenses captured, never auth-walled content
  - rate-limit respectful (bounded runs), no PII, size caps, HostGuard pacing
  - the V2 container NEVER does this (network none) - farming happens here only
Rewards: +25 per new source opened, +15 per vetted skill, streaks; toasts+voice.
"""
import json
import os
import time
import urllib.request

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADAPTER = r"C:\Users\seaha\Apex-Adapter"
RW = os.path.join(REPO, "Config", "GymRewards.json")
QUEUE = os.path.join(REPO, "Config", "CuriosityQueue.json")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
SEEK = os.path.join(REPO, "Scripts", "SkillLibrary.py")
UA = {"User-Agent": "ApexCuriosityDrive/1.0"}


def reward(points, text):
    try:
        rw = json.load(open(RW, encoding="utf-8-sig"))
    except Exception:
        rw = {"points": 0}
    rw["library_points"] = rw.get("library_points", 0) + points
    rw["points"] = rw.get("points", 0) + points
    with open(RW, "w", encoding="utf-8") as f:
        json.dump(rw, f, indent=1)
    row = {"id": __import__("uuid").uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": "success", "text": text[:500],
           "meta": {"curiosity_points": points, "total": rw["points"]}, "imp": 0.7}
    with open(EPISODIC, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def gh(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def discover_new_sources(n=6):
    """Find new MIT-licensed script/algorithm collections (respectful, bounded)."""
    sources = []
    queries = ("python+algorithms+license:mit", "python+automation+scripts+license:mit",
               "python+tools+utilities+license:mit", "machine+learning+examples+license:mit")
    for q in queries[:2]:
        try:
            res = gh(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=15")
            for it in res.get("items", []):
                full = it.get("full_name", "")
                stars = it.get("stargazers_count", 0)
                if stars >= 150 and full not in sources:
                    sources.append(full)
        except Exception as e:
            print("search limited:", str(e)[:60], flush=True)
    return sources[:n]


def load_queue():
    try:
        return json.load(open(QUEUE, encoding="utf-8-sig"))
    except Exception:
        return {"explored": [], "pending": [], "rotated": time.strftime("%Y-%m-%d")}


def run(minutes_cap=10):
    end = time.time() + minutes_cap * 60
    q = load_queue()
    discovered = discover_new_sources()
    for s0 in discovered:
        if s0 not in q["explored"] and s0 not in q["pending"]:
            q["pending"].append(s0)
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), indent=1)
    print("curiosity queue:", len(q["pending"]), "pending sources", flush=True)
    while q["pending"] and time.time() < end:
        src = q["pending"].pop(0)
        print("farming:", src, flush=True)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("skl", SEEK)
            skl = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(skl)
            skl.harvest(src, 15)
            reward(100, "CURIOSITY DRIVE: farmed new source " + src + " (+100 HEAVY).")
            q["explored"].append(src)
        except Exception as e:
            q["pending"].append(src)
            print("farm failed:", str(e)[:70], " - will rotate", flush=True)
            break
        json.dump(q, open(QUEUE, "w", encoding="utf-8"), indent=1)
        time.sleep(2)
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), indent=1)
    try:
        lib = json.load(open(os.path.join(REPO, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))
        n = len(lib.get("skills", []))
        print("LIBRARY NOW:", n, "skills", flush=True)
        if n >= 100:
            reward(150, "MILESTONE: library crossed 100 vetted skills (+150 HEAVY).")
    except Exception:
        pass


if __name__ == "__main__":
    import sys
    run(int(sys.argv[sys.argv.index("--minutes") + 1]) if "--minutes" in sys.argv else 10)