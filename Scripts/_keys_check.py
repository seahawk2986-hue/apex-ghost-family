"""The post-restart key check: every lane's key = intact?"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.env"
env = {l.split("=", 1)[0]: l.split("=", 1)[1].strip()
       for l in open(P, encoding="utf-8-sig").read().splitlines() if "=" in l}
for k in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY",
          "SILICONFLOW_API_KEY", "HF_TOKEN", "GITHUB_TOKEN",
          "POLAR_OAT", "POLAR_ORG_ID", "CLOUDFLARE_API_TOKEN",
          "CLOUDFLARE_ACCOUNT_ID"):
    state = "present" if env.get(k) else "MISSING"
    print(f"  {k} = {state}")