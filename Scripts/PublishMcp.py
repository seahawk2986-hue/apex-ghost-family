"""PUBLISH THE FAMILY ON SMITHERY (the founder-run last step):
reads SMITHERY_API_KEY from .env (values never printed) and runs the real
publish: npx @smithery/cli mcp publish server.mcpb -n seahawk2986-hue/apex-ghost-family
Non-interactive. Prints the CLI's output honestly.
FOUNDER'S 3 STEPS (browser, ~3 min, once):
 1. open https://smithery.ai  -> Sign in (GitHub OAuth as seahawk2986-hue)
 2. open https://smithery.ai/account/api-keys -> Create API key -> copy it
 3. add one line to .env:  SMITHERY_API_KEY=pasted_here
Then say the word - this script publishes (or run: python Scripts/PublishMcp.py)."""
import json
import os
import subprocess
import sys
import urllib.request

ROOT = R_C = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
BUNDLE = os.path.join(ROOT, "server.mcpb")
NAME = "seahawk2986-hue/apex-ghost-family"


def smithery_key():
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        if line.strip().startswith("SMITHERY_API_KEY="):
            v = line.partition("=")[2].strip()
            if v:
                return v
    return None


def publish():
    key = smithery_key()
    if not key:
        print("[publish] SMITHERY_API_KEY not in .env yet - the 3 founder steps above")
        print("[publish] (the key lives in .env only - never chat; I read it from there)")
        return 1
    if not os.path.exists(BUNDLE):
        print("[publish] server.mcpb missing - run ApexMcpServer.py --build-mcpb first")
        return 1
    env = dict(os.environ, SMITHERY_API_KEY=key)
    print("[publish] key present (fingerprint masked) - publishing "
          f"{os.path.basename(BUNDLE)} as {NAME} (non-interactive)...")
    try:
        r = subprocess.run(
            ["npx", "-y", "@smithery/cli@latest", "mcp", "publish", BUNDLE, "-n", NAME],
            capture_output=True, text=True, timeout=300, env=env,
            shell=True if os.name == "nt" else False)
        out = (r.stdout or "") + (r.stderr or "")
        print(out.strip()[-1200:])
        soft_fail = ("✗" in out) or ("must include" in out.lower()) or \
                    ("error" in out.lower() and "success" not in out.lower()) or \
                    r.returncode != 0
        if soft_fail:
            print(f"[publish] FAILED honestly (rc={r.returncode}) - the validator's "
                  f"message is above; iterating the bundle fixes it")
            return 1
        print(f"[publish] rc={r.returncode} - if the output above shows a listing/success, "
              f"the family is LISTED; verify with PublishMcp.py --check")
        return 0
    except Exception as e:
        print(f"[publish] attempt failed honestly: {str(e)[:100]}")
        return 1


if __name__ == "__main__":
    if "--check" in sys.argv:
        try:
            with urllib.request.urlopen("https://smithery.ai/servers?q=apex",
                                        timeout=15) as resp:
                body = resp.read().decode("utf-8", "ignore")
            print("listed check: 'apex-ghost-family' found in registry:" if
                  "apex-ghost-family" in body.lower() else
                  "not listed yet (or page format changed) - honest")
        except Exception as e:
            print("listed-check failed:", str(e)[:80])
        sys.exit(0)
    sys.exit(publish())