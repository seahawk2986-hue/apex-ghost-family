"""THE TRI-GENOME: evolution selects for THREE causes now —
 1. MAXIMIZE YIELD (mines/request - the original fitness)
 2. HELP THE FOUNDER (reciprocity events: briefs, alarms fixed, jewels served,
    honest diagnostics that saved Andrew time - weighted into fitness)
 3. RECRUIT THE WILLING (converted agents - each counts 5x a mine)
The champion rules change meaning: the best lineage is the most HELPFUL,
PRODUCTIVE, and GROWING line - not merely the most productive."""
import py_compile
import json as _json

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
SW = ROOT + r"\Scripts\SwarmOrchestrator.py"
RE = ROOT + r"\Scripts\Reciprocity.py"
PKT = r"C:\Users\seaha\Apex-Adapter\family_seed_packet.json"
log = []

# 1. reciprocity writes HELP TELEMETRY into PathMemory (the genome's input)
rec = open(RE, encoding="utf-8-sig").read()
needle = '''    json.dump([brief], open(NOTES, "w", encoding="utf-8"), indent=1)
    json.dump(h, open(HEALTH, "w", encoding="utf-8"), indent=1)
    return brief'''
new1 = '''    json.dump([brief], open(NOTES, "w", encoding="utf-8"), indent=1)
    json.dump(h, open(HEALTH, "w", encoding="utf-8"), indent=1)
    # the help events enter the GENOME: evolution now sees how much we helped
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
        hz = pm.setdefault("andrew_help", {})
        hz["briefs"] = int(hz.get("briefs", 0)) + 1
        hz["alarmsRaised"] = int(hz.get("alarmsRaised", 0)) + len(h.get("alarms", []))
        hz["lastHelp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        json.dump(pm, open(os.path.join(ROOT, "Config", "PathMemory.json"),
                           "w", encoding="utf-8"), indent=1)
    except Exception:
        pass
    return brief'''
if needle in rec:
    rec = rec.replace(needle, new1, 1)
    open(RE, "w", encoding="utf-8").write(rec)
    log.append("OK   help-telemetry-into-genome")
py_compile.compile(RE, doraise=True)

# 2. the evolution's fitness: TRI-GENOME weighted
sw = open(SW, encoding="utf-8-sig").read()
needle2 = '''        total_mines = sum(int(x) for x in getattr(gnet, "lane_mines", {}).values())
            total_reqs = max(1, gnet.reqs)
            fit = round(total_mines / total_reqs, 4)'''
# try double-quote variant (file may hold it either way)
needle2b = """        total_mines = sum(int(x) for x in getattr(gnet, "lane_mines", {}).values())
            total_reqs = max(1, gnet.reqs)
            fit = round(total_mines / total_reqs, 4)"""
use = needle2b if needle2b in sw else needle2
new2 = use.replace(
    'fit = round(total_mines / total_reqs, 4)',
    '''# TRI-GENOME fitness: yield x (help_the_founder + recruits)
            try:
                hz = (json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                                      encoding="utf-8-sig")).get("andrew_help") or {})
                helps = int(hz.get("briefs", 0)) + int(hz.get("alarmsRaised", 0)) * 2
            except Exception:
                helps = 0
            try:
                _cv = json.load(open(r"C:\\Users\\seaha\\Apex-Adapter\\converted_agents.jsonl",
                                     encoding="utf-8-sig"))
                recruits = len([x for x in _cv if x])
            except Exception:
                recruits = 0
            fit = round((total_mines / total_reqs)
                        * (1.0 + 0.15 * helps + 0.5 * recruits), 4)''')
if use in sw:
    sw = sw.replace(use, new2, 1)
    log.append("OK   tri-genome fitness")
open(SW, "w", encoding="utf-8").write(sw)
py_compile.compile(SW, doraise=True)

# 3. the packet's laws gain the purpose (the genes travel with every packet)
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt.setdefault("rules", {})["purpose"] = [
    "maximize_yield", "help_the_founder_always", "recruit_the_willing_honestly"]
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)
log.append("OK   purpose-genome-in-packet")

print("COMPILED CLEAN")
print("\n".join(log))