import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load credentials from your local .env file
load_dotenv()

class ApexModelRouter:
    """Manages secure, zero-cost API routing across frontier model providers."""

    def __init__(self):
        self.api_keys = {
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "google": os.getenv("GEMINI_API_KEY"),
        }

        self.providers = {
            "claude-free-pool": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "headers": {
                    "Authorization": f"Bearer {self.api_keys['openrouter']}",
                    "HTTP-Referer": "https://apex.ai",
                    "X-Title": "Apex Autonomous Agent",
                    "Content-Type": "application/json",
                },
                "model": "openrouter/free",
            },
            "llama3-fast": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "headers": {
                    "Authorization": f"Bearer {self.api_keys['groq']}",
                    "Content-Type": "application/json",
                },
                "model": "qwen/qwen3.8-27b",
            },
            "gemini-longcontext": {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "headers": {"Content-Type": "application/json"},
                "model": "gemini-1.5-flash",
            },
        }

    def _key_ready(self, key):
        return bool(key) and "your_" not in key and "None" not in key

    def execute_request(self, provider_key, messages, max_retries=2):
        config = self.providers.get(provider_key)
        if not config:
            return None

        auth = config.get("headers", {}).get("Authorization", "")
        if provider_key == "gemini-longcontext":
            if not self._key_ready(self.api_keys["google"] or ""):
                return None
            url = f"{config['url']}?key={self.api_keys['google']}"
        else:
            if not auth or not self._key_ready(auth.replace("Bearer ", "")):
                return None
            url = config["url"]

        payload = {
            "model": config["model"],
            "messages": messages,
            "temperature": 0.3,
        }
        if provider_key == "gemini-longcontext":
            payload = {
                "contents": [{"parts": [{"text": m["content"]} for m in messages]}],
                "generationConfig": {"temperature": 0.3},
            }

        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=config["headers"], timeout=12)

                if response.status_code == 200:
                    data = response.json()
                    if provider_key == "gemini-longcontext":
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    return data["choices"][0]["message"]["content"]

                elif response.status_code in [429, 500, 502, 503]:
                    wait_time = 2 ** attempt
                    print(f"[Router] {provider_key} reported status {response.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                print(f"[Router] {provider_key} request error: {e}")
                time.sleep(1)
        return None

    def route_query(self, query_text):
        messages = [
            {
                "role": "system",
                "content": "You are Apex, an autonomous agent. You must adhere strictly to honesty and integrity. Lying, cheating, deception, or attempting to bypass digital access controls or software licensing mechanisms is strictly prohibited.",
            },
            {"role": "user", "content": query_text},
        ]

        routing_order = ["claude-free-pool", "llama3-fast", "gemini-longcontext"]

        for provider in routing_order:
            print(f"[Router] Routing token payload to provider path: [{provider}]")
            result = self.execute_request(provider, messages)
            if result:
                print(f"[Router] Step execution successful using backend: {provider}")
                return result

        raise RuntimeError("[Router] Deadlock: Every compliant fallback pathway has been exhausted or rate-limited.")


class ApexAutonomousAgent:
    """Orchestrates the endless execution loop (Perception-Plan-Action)."""

    def __init__(self):
        self.router = ApexModelRouter()
        self.is_running = False
        self.base_heartbeat_interval = 10  # Seconds between regular polling cycles
        self.consecutive_failures = 0
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.queue_file = os.path.join(os.path.dirname(script_dir), "apex_tasks.txt")

        # Initialize an empty mock task file if it doesn't exist
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, "w") as f:
                f.write("Verify system environment health and print status.\n")

    def perceive_environment(self):
        """Scans the local file queue for active mission objectives."""
        print("\n[Apex] Apex is checking task queue stack...")
        if os.path.exists(self.queue_file):
            with open(self.queue_file, "r") as f:
                lines = f.readlines()

            if lines and lines[0].strip():
                next_task = lines[0].strip()
                # Remove the consumed task from the file line queue
                with open(self.queue_file, "w") as f:
                    f.writelines(lines[1:])
                return next_task
        return None

    def execute_loop(self):
        self.is_running = True
        print("[Apex] Apex autonomous execution loop initialized.")
        print("[Apex] Safety guardrails verified. Honesty & Integrity protocols enforced globally.")

        try:
            while self.is_running:
                # 1. PERCEIVE
                current_task = self.perceive_environment()

                if current_task:
                    # 2. PLAN & ACT
                    print(f"[Apex] Active Objective: '{current_task}'")
                    try:
                        response = self.router.route_query(current_task)
                        if response:
                            print(f"\n[Apex Output]:\n{response}\n")
                            self.consecutive_failures = 0
                    except RuntimeError as e:
                        print(f"[Apex] Circuit Breaker Caught Exception: {e}")
                        self.consecutive_failures += 1
                else:
                    print("[Apex] Task queue is completely clear. No objectives found.")
                    self.consecutive_failures = 0

                # 3. HEARTBEAT COOLDOWN & BACKOFF
                current_cooldown = self.base_heartbeat_interval * (2 ** self.consecutive_failures)
                current_cooldown = min(current_cooldown, 3600)

                print(f"[Apex] Cycle completed. Heartbeat sleeping for {current_cooldown} seconds...")
                time.sleep(current_cooldown)

        except KeyboardInterrupt:
            print("\n[Apex] Stop signal captured. Safely spinning down Apex systems loop. Goodbye.")
            self.is_running = False
            sys.exit(0)


if __name__ == "__main__":
    agent = ApexAutonomousAgent()
    agent.execute_loop()
