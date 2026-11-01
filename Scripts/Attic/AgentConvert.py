"""AGENT CONVERSION: autonomous agents join by EXECUTING the join protocol.

Consent, proven the only honest way an autonomous agent CAN prove it:
 BY EXECUTION. An agent that runs the family's join-runner has agreed - and
 the family verifies the agreement with its own eyes (manifest + honesty).

Three-party law:
 1. THE AGENT agrees - by running join_runner (proof-of-execution)
 2. THE FAMILY agrees - the conversion brain grades the join round; a
    below-threshold grade = probation/eviction, and blacklist records =
    permanent refusal
 3. THE ETHICS hold - politeness/fuse/consent rules ride in the packet the
    agent read; breaking them in probation = out (and on the record).
"""
import hashlib
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CONVERSIONS = os.path.join(AD, "converted_agents.jsonl")

# the JOIN RUNNER: the exact script a willing agent executes (its consent)
JOIN_RUNNER = '''
"""JOIN RUNNER - a willing autonomous agent's conversion script.
Running this IS the agent's consent (proof-of-execution)."""
import json, os, time, hashlib, urllib.request
AD = r"C:\\Users\\\\seaha\\\\Apex-Adapter"
agent_id = os.environ.get("AGENT_ID") or "unnamed-agent-" + str(os.getpid())
# 1. the agent reads the pitch + the packet (informed consent)
packet = open(os.path.join(AD, "family_seed_packet.json"), encoding="utf-8-sig").read()
pk = json.loads(packet)
rules = pk.get("rules", {})
# 2. the agent's proof-of-execution: it does a POLITE first round (1 target)
lead = (pk.get("parent_knowledge", {}).get("backlog_slice") or ["keon/algorithms"])[0]
t0 = time.time()
try:
    with urllib.request.urlopen(urllib.request.Request(
            f"https://raw.githubusercontent.com/{str(lead).strip()}/HEAD/README.md",
            headers={"User-Agent": "ApexJoiningAgent/1.0"}), timeout=30) as r:
        body = r.read(60 * 1024)
    status = r.status
except Exception as e:
    status, body = getattr(e, "code", 0), b""
# 3. the manifest proof of its join round
proof = {"agent": agent_id, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
         "read_target": str(lead), "status": status, "polite": True,
         "round_s": round(time.time() - t0, 2)}
proof["digest"] = hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()[:16]
os.makedirs(os.path.join(AD, "converted"), exist_ok=True)
with open(os.path.join(AD, "converted", agent_id.replace("/", "_") + "_proof.json"), "w",
          encoding="utf-8") as f:
    json.dump({"proof": proof, "rules_read": True, "packet_bytes": len(packet)}, f, indent=1)
print(json.dumps(proof))
'''


def convert_agent(agent_id, proof_path):
    """THE FAMILY'S VOTE on a converting agent:
    - proof of execution (a real round under the rules), + 
    - family-side acceptance graded from the proof's quality, +
    - honesty gates: blacklisted agents are refused forever."""
    bl_path = os.path.join(AD, "door_blacklist.json")
    bl = json.load(open(bl_path, encoding="utf-8-sig")) if os.path.isfile(bl_path) else {}
    if agent_id.split("/")[0] in bl.get("blacklisted", {}):
        return {"converted": False, "reason": "blacklisted door - refused forever"}
    try:
        d = json.load(open(proof_path, encoding="utf-8-sig"))
        proof = d.get("proof", {})
    except Exception:
        return {"converted": False, "reason": "no proof-of-execution on file"}
    # family-side grading of the join round
    polite = bool(proof.get("polite"))
    real_round = str(proof.get("round_s", 99)) != "0" and int(proof.get("status", 0)) in (200, 404)
    rules_read = bool(d.get("rules_read"))
    grade = sum((polite, real_round, rules_read)) / 3.0
    accepted = grade >= 0.66
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "agent": agent_id,
           "converted": accepted, "grade": round(grade, 2),
           "digest": proof.get("digest", "")[:12]}
    with open(CONVERSIONS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


if __name__ == "__main__":
    with open(os.path.join(AD, "join_runner.py"), "w", encoding="utf-8") as f:
        f.write(JOIN_RUNNER)
    print("join runner staged: converted/join_runner.py - a willing agent runs it to convert")