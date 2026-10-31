"""
ApexTierScout - Autonomous free-tier discovery.

What it does (all legitimate, official endpoints only):
  1. LIVE-scans OpenRouter's public model catalog (no key required) and detects
     every model currently offered on the free tier (":free" suffix). Free
     models appear/disappear often, so this is re-runnable any time.
  2. Merges the static directory of official signup pages (human does the
     one-time signup; Apex only discovers and reports).
  3. Writes Config/FreeTierCatalog.json for the router and prints a summary.

It never scrapes, guesses, or hunts for keys. Discovery only.
"""

import json
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Config", "FreeTierCatalog.json")

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Official signup pages: the human creates the account, ONE time.
SIGNUP_DIRECTORY = {
    "OpenRouter": {
        "signup": "https://openrouter.ai/settings/keys",
        "note": "Largest free pool: 50+ models with :free suffix (DeepSeek, Llama, Qwen, Gemini)",
    },
    "Groq": {
        "signup": "https://console.groq.com/keys",
        "note": "Very fast Llama 3.x / Mixtral inference, generous free rate limits",
    },
    "Google Gemini": {
        "signup": "https://aistudio.google.com/apikey",
        "note": "Gemini Flash free tier, huge context window",
    },
    "Mistral": {
        "signup": "https://console.mistral.ai/api-keys",
        "note": "Free tier on La Plateforme after phone verify",
    },
    "Cerebras": {
        "signup": "https://cloud.cerebras.ai/",
        "note": "Free tier, extremely fast Llama inference",
    },
    "Cohere": {
        "signup": "https://dashboard.cohere.com/api-keys",
        "note": "Free trial keys, Command-R models",
    },
    "GitHub Models": {
        "signup": "https://github.com/settings/personal-access-tokens",
        "note": "Free with any GitHub account; GPT-4o/DeepSeek/Llama via GitHub",
    },
    "HuggingFace": {
        "signup": "https://huggingface.co/settings/tokens",
        "note": "Free monthly inference credits on serverless endpoints",
    },
}


def scan_openrouter_free():
    """Live: return the current list of free-tier models on OpenRouter."""
    try:
        r = requests.get(OPENROUTER_MODELS_URL, timeout=20,
                         headers={"User-Agent": "ApexTierScout/1.0"})
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        models = r.json().get("data", [])
        free = []
        for m in models:
            mid = m.get("id", "")
            if mid.endswith(":free"):
                free.append({
                    "id": mid,
                    "context": m.get("context_length"),
                    "name": m.get("name", ""),
                })
        return free, None
    except requests.RequestException as e:
        return None, str(e)


def main():
    print("[Scout] Scanning official free-tier catalogs (discovery only)...")
    catalog = {
        "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "signup_directory": SIGNUP_DIRECTORY,
        "openrouter_free_models": [],
        "scan_error": None,
    }

    free, err = scan_openrouter_free()
    if err:
        catalog["scan_error"] = f"OpenRouter scan failed: {err}"
        print(f"[Scout] OpenRouter live scan failed: {err}")
    else:
        catalog["openrouter_free_models"] = free
        print(f"[Scout] OpenRouter free tier: {len(free)} models live right now")
        for m in free[:12]:
            print(f"    - {m['id']} (ctx {m['context']})")
        if len(free) > 12:
            print(f"    ... and {len(free) - 12} more")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"[Scout] Catalog saved -> {OUT}")
    print("[Scout] Next step (human, one-time): create keys at the signup pages above,")
    print("        then put them in the .env file. Apex routes everything after that.")


if __name__ == "__main__":
    main()
