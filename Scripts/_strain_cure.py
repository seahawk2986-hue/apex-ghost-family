"""THE STRAIN-CURE BUNDLE (the founder's screenshot = the family's honest
recall: RAM 1.93GB < 2.0 = the pacing = ENGAGED = CORRECT behavior):
(1) the NOW-ram; (2) the ChatEval gains the load-gate (>= 2.2 + the
between-lanes gap); (3) the DesignV3's 3-tuples flattened (the regex-cure
the notes after not-applicable die)."""
import json
import re
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
import psutil

vm = psutil.virtual_memory()
ram = vm.available / 2**30
print(f"[strain-cure] RAM NOW: {ram:.2f}GB free / "
      f"{vm.total/2**30:.0f}GB - "
      f"{'OK' if ram >= 2.2 else 'STILL-PACED (the guard = honest)'}")

# (3) the DesignV3's cure (the byte-regex)
p = ROOT + r"\Scripts\DesignV3.py"
t = open(p, encoding="utf-8").read()
t2 = re.sub(r'("not-applicable"),\s*"[^"]*"\)', r"\1)", t)
if t2 != t:
    open(p, "w", encoding="utf-8", newline="\n").write(t2)
    print("[strain-cure] DesignV3: the 3-tuples flattened")
else:
    print("[strain-cure] DesignV3: no 3-tuple found (already clean)")

# (2) the ChatEval's gate (the honest: pause-between + the pre-check)
cp = ROOT + r"\Scripts\ChatEval.py"
ct = open(cp, encoding="utf-8").read()
if "def ram_gb" not in ct:
    ct = ct.replace(
        "def ask_local(model, prompt):",
        "def ram_gb():\n"
        "    import psutil\n"
        "    return psutil.virtual_memory().available / 2**30\n"
        "\n\n"
        "def ask_local(model, prompt):")
    ct = ct.replace(
        "for lane, model, kind in LANES:",
        "for lane, model, kind in LANES:\n"
        "            if kind is None and ram_gb() < 2.2:\n"
        "                answers[lane] = \"\"\n"
        "                evalout.setdefault('errs', []).append(\n"
        "                    f'{lane}/ask{ai}: RAM-PAUSED (the "
        "honest gate)')\n"
        "                continue")
    open(cp, "w", encoding="utf-8", newline="\n").write(ct)
    print("[strain-cure] ChatEval: the RAM-gate installed")
else:
    print("[strain-cure] ChatEval: the gate's present")