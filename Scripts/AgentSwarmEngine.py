import os
import json
import httpx

class AgentSwarmEngine:
    def __init__(self, endpoint_url="http://localhost:11434/v1/chat/completions", model="qwen2.5-coder:3b", project_root=""):
        self.url = endpoint_url
        self.model = model
        self.root = project_root
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()

    def _execute_safety_governor_audit(self, script_contents):
        """Component 3: Unalterable Safety Governor (The Non-Negotiables)"""
        print("?? [Safety Governor] Running pre-flight system constraint scans...")
        banned_terms = ["connect-driveagent.ps1", "unauthorized_ip", "admin_password"]
        for term in banned_terms:
            if term in script_contents.lower():
                print(f"? [Safety Governor Block] Found unauthorized system target: '{term}'! Terminating build.")
                return False
        return True

    def execute_synthesis(self, instruction, target_filename):
        print(f"?? [Core Engine] Compiling radical autonomy code blocks for module: '{target_filename}'")
        target_url = self.url if self.api_key else "http://localhost:11434/v1/chat/completions"
        target_model = self.model if self.api_key else "qwen2.5-coder:3b"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        system_prompt = (
            f"Write a master-level PowerShell tool for: {instruction}\n"
            f"Constraint: You must use [CmdletBinding()] and output a structured [PSCustomObject].\n"
            f"Output ONLY executable lines inside a code block, no markdown conversation filler."
        )
        payload = {"model": target_model, "messages": [{"role": "user", "content": system_prompt}], "temperature": 0.2}

        try:
            with httpx.Client(timeout=90.0) as client:
                res = client.post(target_url, json=payload, headers=headers)
                raw_code = res.json()["choices"][0]["message"]["content"].replace("```powershell", "").replace("```", "").strip()
                
                if self._execute_safety_governor_audit(raw_code):
                    return raw_code
                return "# Safety Governor Protection Violation Blocked Implementation Script."
        except Exception as e:
            return f"# Autonomy Engine Matrix Exception: {str(e)}"

    def execute_self_repair(self, original_code, error_trace):
        print("?? [Sandbox Remediation] Parsing crash log variables. Regenerating code assets...")
        target_url = self.url if self.api_key else "http://localhost:11434/v1/chat/completions"
        target_model = self.model if self.api_key else "qwen2.5-coder:3b"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        repair_prompt = f"Fix this PowerShell syntax error.\nError Trace:\n{error_trace}\nCode:\n{original_code}\nOutput valid code only."
        payload = {"model": target_model, "messages": [{"role": "user", "content": repair_prompt}], "temperature": 0.1}
        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(target_url, json=payload, headers=headers)
                return res.json()["choices"][0]["message"]["content"].replace("```powershell", "").replace("```", "").strip()
        except Exception:
            return original_code

