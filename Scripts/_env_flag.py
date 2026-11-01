"""THE FREE-TIER FLAG (the founder's explicit opt-in, honored in .env):
appends CLOUD_ALLOWED=1 (the no-card free tiers ONLY; the credits tier
stays behind CREDITS_ALLOWED - the never-printed, never-committed line)."""
import os

P = os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", ".env")
t = open(P, encoding="utf-8-sig").read() if os.path.exists(P) else ""
if "CLOUD_ALLOWED" not in t:
    with open(P, "a", encoding="utf-8") as f:
        f.write("\nCLOUD_ALLOWED=1\n")
    print("[env-flag] CLOUD_ALLOWED=1 appended (the no-card free tiers "
          "now serve; the credits tier still sleeps)")
else:
    print("[env-flag] CLOUD_ALLOWED present (idempotent)")