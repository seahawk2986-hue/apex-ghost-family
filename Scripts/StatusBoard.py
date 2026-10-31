"""THE STATUS BOARD: every family system's live state, refreshed every 30s."""
import json
import os
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
BOARD = os.path.join(AD, "family_status_board.json")


def read_board_once():
    b = {"updated": time.strftime("%Y-%m-%d %H:%M:%S")}
    b["ram_free_gb"] = round(psutil.virtual_memory().available / 1024 ** 3, 2)
    b["brain"] = {"pid_count": 0, "ram_mb": 0}
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            if p.info["name"] and p.info["name"].lower().startswith("llama-server"):
                b["brain"]["pid_count"] += 1
                b["brain"]["ram_mb"] += p.info["memory_info"].rss // 1024 ** 2
        except Exception:
            pass
    for path, key in ((AD + r"\swarm_state.json", None),):
        try:
            st = json.load(open(path, encoding="utf-8-sig"))
            b["backlog"] = len(st.get("pending_leads", []))
            b["repos_consumed"] = len(st.get("repos", []))
            b["last_round"] = st.get("last_run", "?")
        except Exception:
            b["backlog"] = b["repos_consumed"] = -1
    try:
        b["skills"] = len(json.load(open(ROOT + r"\Config\SkillLibrary.json",
                                         encoding="utf-8-sig"))["skills"])
    except Exception:
        b["skills"] = -1
    try:
        cl = json.load(open(ROOT + r"\Config\CryptoLedger.json", encoding="utf-8-sig"))
        b["money"] = f"${float(cl.get('earned', 0)) - float(cl.get('spent', 0)):.2f}"
    except Exception:
        b["money"] = "$0.00"
    try:
        pm = json.load(open(ROOT + r"\Config\PathMemory.json", encoding="utf-8-sig"))
        b["lanes_learning"] = len([k for k in pm if k not in (
            "grading", "use", "farm", "variants", "family", "andrew_help", "finance",
            "finance_kit", "finance_kit_kit")])
        b["briefs_for_andrew"] = (pm.get("andrew_help") or {}).get("briefs", 0)
        b["converts"] = sum(1 for _l in open(AD + r"\converted_agents.jsonl",
                                             encoding="utf-8-sig") if _l.strip())
    except Exception:
        b["lanes_learning"] = 0
    b["hub_doors"] = {"staged": 4, "joined": 0, "knocks": "polite, every 24h"}
    try:
        hf = os.path.getsize(ROOT + r"\..\.lmstudio\models" if os.path.isdir(
            ROOT + r"\..\.lmstudio\models") else r"C:\Users\seaha\.lmstudio\models")
    except Exception:
        hf = None
    return b


if __name__ == "__main__":
    deadline = time.time() + int(os.environ.get("BOARD_MINUTES", "60")) * 60
    while time.time() < deadline:
        b = read_board_once()
        try:
            json.dump(b, open(BOARD, "w", encoding="utf-8"), indent=1)
            print(json.dumps(b), flush=True)
        except Exception:
            pass
        time.sleep(30)