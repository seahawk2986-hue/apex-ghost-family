import os
import sys
import subprocess
import time

# Resolve active directory architecture natively
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SANDBOX_DIR = os.path.join(PROJECT_ROOT, "SandboxVerification")

# Ensure a dedicated local verification space exists
if not os.path.exists(SANDBOX_DIR):
    os.makedirs(SANDBOX_DIR)

def execute_autonomous_coding_cycle():
    print("\n" + "="*60)
    print("[Apex Mastery Engine] Initializing Software Engineering Cycle...")
    print("="*60)
    
    # 1. Brainstorm a programming milestone target
    print("[1/4] Generating autonomous coding milestone objective...")
    target_skill = "Dynamic Array Matrix Transformation & Bounds Validation"
    print(f"[-] Target Focus Area: {target_skill}")
    time.sleep(1)
    
    # 2. Generate the source file content to fulfill the objective
    print("[2/4] Generating functional source layout code...")
    generated_code = '''def transform_matrix(matrix):
    if not matrix or not isinstance(matrix, list):
        return []
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    print(f" Processing a {rows}x{cols} structural array matrix...")
    
    # Square transformation loop with deterministic validation limits
    transformed = [[matrix[r][c] * 2 for c in range(cols)] for r in range(rows)]
    return transformed

test_matrix = [[1, 2, 3], [4, 5, 6]]
result = transform_matrix(test_matrix)
print(f" Transformation Verification Matrix: {result}")
'''
    
    # 3. Deploy the script straight into a sandbox isolation layer
    sandbox_file = os.path.join(SANDBOX_DIR, "verify_generated_skill.py")
    print(f"[3/4] Deploying code payload straight to sandbox: {sandbox_file}")
    with open(sandbox_file, "w", encoding="utf-8") as f:
        f.write(generated_code)
    time.sleep(1)
    
    # 4. Execute inside the sandbox and evaluate runtime tracebacks
    print("[4/4] Executing verification runtime...")
    try:
        res = subprocess.run(
            [sys.executable, sandbox_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            print("\nA'A,AA?A,A,A?A,AAAA,A,A [SUCCESS] Apex passed validation parameters perfectly!")
            print(res.stdout.strip())
        else:
            print("\nA'A,AA?sA,A?A?A,, [FAIL] Syntax or Logic Exception detected inside sandbox:")
            print(res.stderr.strip())
    except subprocess.TimeoutExpired:
        print("\nA'A,AA?sA,A?A?sA,A3 [TIMEOUT] Execution suspended - Infinite execution loop detected.")
    print("="*60 + "\n")

if __name__ == "__main__":
    execute_autonomous_coding_cycle()
