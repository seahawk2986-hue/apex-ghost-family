"""THE VOICE-ON CURE: flip speak_replies=true in the ears' config, restart
the ears cleanly, warm the speak-organ once (the audible ping = YOUR proof)."""
import json
import os
import subprocess as sp
import sys
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)

# 1. the config-flip (the one-flag-cure)
CP = os.path.join(ROOT, "Config", "ApexEars.json")
c = json.load(open(CP, encoding="utf-8-sig"))
c["speak_replies"] = True
json.dump(c, open(CP, "w", encoding="utf-8"), indent=1)
print('[config] speak_replies =', c["speak_replies"], "(the reply-speaker = ON)")

# 2. the ears-restart (the = the = the config = read per-command by some
# ears-lanes; the restart = the guaranteed pickup)
victims = []
for p in psutil.process_iter(["pid", "cmdline"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        if "ApexEars" in cl and "powershell" in (p.info["name"] or "").lower():
            victims.append(p.info["pid"])
            p.kill()
    except Exception:
        pass
print("[ears restarted]:", victims or "(none were running as powershell)")
sp.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
          "-WindowStyle", "Hidden", "-File",
          os.path.join(ROOT, "Scripts", "ApexEars.ps1")],
         cwd=ROOT, creationflags=0x00000008)
print("[ears] relaunched detached (the wake = listening)")

# 3. THE SPEAK-PROBE: the organ's first real words = the audible proof
r = sp.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", os.path.join(ROOT, "Scripts", "ApexSpeak.ps1"),
            "-Text", "Voice lane online. I am Apex. I will answer out loud "
                     "from now on. Say stop, any time, and I will listen.",
            "-NoWatch"], capture_output=True, text=True, timeout=120)
tail = (r.stdout or "").strip().splitlines()[-3:]
print("[speak-probe]:")
for l in tail:
    print("  ", l[:110])