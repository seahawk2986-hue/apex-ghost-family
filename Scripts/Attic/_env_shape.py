import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
env = open(os.path.join(ROOT, ".env"), encoding="utf-8-sig").read()
lines = [l for l in env.splitlines() if "POLAR" in l.upper()]
print(f"{len(lines)} polar-line(s) in .env:")
for l in lines:
    name, sep, val = l.partition("=")
    val = val.strip().strip('"').strip("'")
    shape_ok = (sep == "=" and " " not in val and val.isascii())
    print(f"  {name.strip()}: len={len(val)} | prefix={val[:10]!r} | "
          f"tail={val[-3:]!r} | ascii-clean={val.isascii()} | "
          f"no-space={' ' not in val}")
all_env = [n.split('=')[0] for n in env.splitlines() if '=' in n and n.strip()]
print("the .env's key-names:", all_env)