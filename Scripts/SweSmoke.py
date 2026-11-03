"""SweSmoke - THE FAMILY'S SWE-CLASS DRILL COURT (2026-11-04, the A+ round).

THE LAST RED AXIS (the verified scorecard): no external-class SWE score.
THE DOCTRINE (verified today): mini-swe-agent v2 (2.4.6, MIT, >74%
SWE-bench Verified) with ONE tool (bash), a LINEAR history, and fully
INDEPENDENT per-action runs. The family installs mini ITSELF and gives it
a court: the AGENT LOOP on the host (the fleet's free lanes answer it);
EVERY ACTION inside the SEALED court (docker run --rm --network none
--read-only --tmpfs /tmp -v task): the TASK = one seeded-bug snippet + a
pytest file FAILing on the seed - the agent wins by making pytest PASS;
THE VERDICT = the court's own pytest AFTER the agent (the finish-gate law:
only the runtime verdict counts); the receipt rows = Scores/swe_smoke.jsonl
(resolved, wall_s = the per-task METR-horizon timer, turns, lane); the
cumulative resolved% = the family's daily SWE-class score.
$0 lanes only; <= 3 tasks/beat; fail-closed."""
import io
import json
import os
import random
import sys
import tempfile
import time

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(REPO, "Scores", "swe_smoke.jsonl")
TURNS_CAP = 6
TASK_TURNS = 3


class DockerCourt:
    """Mini-env-compatible shim: every action = ONE independent sealed
    container run (the mini doctrine + the family's sandbox law)."""

    IMAGE = "apex/mini-court"

    def __init__(self, taskdir):
        self.taskdir = taskdir
        self.config = type("C", (), {"cwd": "/task"})()

    def _ensure_court_image(self):
        """The court's image: python + pytest provisioned ONCE (the sealed
        beats run --network none; the fix lives IN the image)."""
        import subprocess
        try:
            r = subprocess.run(["docker", "image", "inspect", self.IMAGE],
                               capture_output=True, timeout=20)
            if r.returncode == 0:
                return True
        except Exception:
            return False
        df = os.path.join(tempfile.gettempdir(), "Dockerfile.apex_court")
        try:
            with open(df, "w", encoding="utf-8") as f:
                f.write("FROM python:3.12-slim\nRUN pip install --no-cache-dir pytest pytest-timeout\n")
            r = subprocess.run(["docker", "build", "-t", self.IMAGE,
                                "-f", df, tempfile.gettempdir()],
                               capture_output=True, text=True, timeout=900)
            return r.returncode == 0
        except Exception:
            return False

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None):
        import subprocess
        import minisweagent.exceptions as _ex
        self._ensure_court_image()
        command = (action or {}).get("command", "")
        timeout = timeout or 60
        t0 = time.time()
        try:
            r = subprocess.run(
                ["docker", "run", "--rm", "--network", "none", "--read-only",
                 "--tmpfs", "/tmp", "-v", f"{self.taskdir}:/task",
                 "-w", "/task", self.IMAGE, "sh", "-c", command],
                capture_output=True, text=True, timeout=timeout)
            out = {"output": (r.stdout or "") + (r.stderr or ""),
                   "returncode": r.returncode,
                   "exception_info": "",
                   "wall_s": round(time.time() - t0, 1)}
        except Exception as e:
            out = {"output": "", "returncode": -1,
                   "exception_info": f"court failure: {type(e).__name__}: {str(e)[:80]}",
                   "wall_s": round(time.time() - t0, 1)}
        # THE SUBMIT CONTRACT (mini's law): the echo = the agent claims done;
        # the COURT still re-verifies with its own pytest afterwards.
        lines = (out.get("output") or "").lstrip().splitlines(keepends=True)
        if lines and lines[0].strip() == "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" \
                and out.get("returncode") == 0:
            raise _ex.Submitted(
                {"role": "exit", "content": "".join(lines[1:]),
                 "extra": {"exit_status": "Submitted",
                           "submission": "".join(lines[1:])}})
        return out

    def get_template_vars(self, **kwargs):
        import platform
        u = platform.uname()._asdict()
        return {"cwd": "/task", "system": u.get("system", ""),
                "release": u.get("release", ""), "version": u.get("version", ""),
                "machine": u.get("machine", ""), "environment": "sealed docker court"}

    def serialize(self):
        return {"info": {"config": {"environment_type": "SweSmoke.DockerCourt"}}}


def generate_task(seed_hint=""):
    funcs = [
        ("moving_average",
         "def _buggy(values, window):\n"
         "    out = []\n"
         "    for i in range(len(values)):\n"
         "        chunk = values[max(0, i - window + 1): i + 1]\n"
         "        out.append(sum(chunk) // len(chunk))\n"
         "    return out",
         "[1, 2, 3], 2 -> [1.0, 1.5, 2.5]  # the seed used integer //, the ask = the running mean"),
        ("slugify",
         "def _buggy(name):\n"
         "    return name.lower().replace(' ', '_')",
         "'my repo!' -> 'my_repo_'  # the seed kept punctuation, the ask = slug-ify all non-alnms"),
        ("balance_brackets",
         "def _buggy(s):\n"
         "    depth = 0\n"
         "    for ch in s:\n"
         "        depth += 1 if ch == '(' else (-1 if ch == ')' else 0)\n"
         "    return depth == 0",
         "')(' -> False  # the seed went negative unnoticed"),
        ("last_char",
         "def _buggy(s):\n"
         "    return s[0]",
         "'abc' -> 'c'  # the seed indexed the first char, the ask = the last"),
        ("double_list",
         "def _buggy(items):\n"
         "    out = []\n"
         "    for item in items:\n"
         "        out.append(item)\n"
         "    return out",
         "[1, 2] -> [1, 2, 1, 2]  # the seed appended nothing more; the ask = app+app"),
        ("title_case",
         "def _buggy(s):\n"
         "    return s.upper().replace('A', 'a')\n",
         "'my cat' -> 'My Cat'  # the seed uppercased wrongly; the ask = word-title-case"),
    ]
    name, buggy, ask = random.choice(funcs)
    return {"name": name, "buggy": buggy, "ask": ask}


def build_taskdir(task):
    d = tempfile.mkdtemp(prefix="swesmoke_")
    with open(os.path.join(d, "impl.py"), "w", encoding="utf-8") as f:
        f.write("# The seeded-buggy implementation (the ask: make tests PASS)\n"
                + task["buggy"] + "\n")
    tests = {
        "moving_average": [
            "def test_mean():\n    assert _buggy([1, 2, 3], 2) == [1.0, 1.5, 2.5]",
        ],
        "slugify": [
            "def test_slug():\n    assert _buggy('my repo!') == 'my_repo_'",
        ],
        "balance_brackets": [
            "def test_bal():\n    assert _buggy(')(') is False\n    assert _buggy('(())(') is False",
        ],
        "last_char": [
            "def test_last():\n    assert _buggy('abc') == 'c'",
        ],
        "double_list": [
            "def test_dbl():\n    assert _buggy([1, 2]) == [1, 2, 1, 2]",
        ],
        "title_case": [
            "def test_title():\n    assert _buggy('my cat') == 'My Cat'",
        ],
    }
    with open(os.path.join(d, "test_impl.py"), "w", encoding="utf-8") as f:
        f.write('"""The court\'s tests (the ask: ' + task["ask"][:90] + ')"""\n')
        f.write("from impl import _buggy\n\n")
        f.write("\n\n".join(tests[task["name"]]) + "\n")
    return d


def run_task(task, model_name="groq/openai/gpt-oss-120b"):
    """ONE drill: mini agent (host loop) + the sealed court (in-container
    actions); the row = the receipt."""
    import ApexIO
    _e = ApexIO.env()
    for k in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY"):
        if _e.get(k) and not os.environ.get(k):
            os.environ[k] = _e[k]      # litellm's provider seeds (never printed)
    taskdir = build_taskdir(task)
    env = DockerCourt(taskdir)
    t0 = time.time()
    resolved, submission, turns = False, "", 0
    row = {"task": task["name"], "model": model_name,
           "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.models.litellm_model import LitellmModel
        from minisweagent.exceptions import Submitted as _Sub
        SYSTEM = (
            "You are a helpful assistant that can interact with a computer.\n\n"
            "Your response must contain exactly ONE bash code block with ONE command "
            "(or commands connected with && or ||).\n"
            "Include a THOUGHT section before your command where you explain your "
            "reasoning process.\nFormat your response as shown in <format_example>.\n\n"
            "<format_example>\n"
            "Your reasoning and analysis here. Explain why you want to perform the action.\n\n"
            "```mswea_bash_command\nyour_command_here\n```\n"
            "</format_example>\n\n"
            "Failure to follow these rules will cause your response to be rejected.")
        INSTANCE = (
            "Please solve this issue: {{task}}\n\n"
            "You can execute bash commands and edit files (the working dir = /task).\n"
            "Recommended flow: (1) read test_impl.py + impl.py, (2) fix impl.py in place, "
            "(3) run `python -m pytest -q` (pytest IS preinstalled in this court), "
            "(4) verify, (5) finish by issuing exactly: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n"
            "Rules: every response = exactly ONE action in triple backticks; each action "
            "runs in a NEW subshell - combine with && when needed. Do not modify the test.")
        task_prompt = (
            "Make the failing test PASS by fixing impl.py's _buggy function "
            "(edit the file in place; do not change the test). THE ASK: "
            + task["ask"][:90])
        try:
            agent = DefaultAgent(
                LitellmModel(model_name=model_name), env,
                system_template=SYSTEM, instance_template=INSTANCE,
                step_limit=TURNS_CAP, cost_limit=3.0,
                wall_time_limit_seconds=540)
            res = agent.run(task_prompt) or {}
        except _Sub as sub:
            res = (sub.args[0] if sub.args else {})
            res = res if isinstance(res, dict) else {}
        extra = res.get("extra") or {}
        submission = str(extra.get("exit_status") or res.get("exit_status", ""))[:40]
        turns = int(res.get("n_calls") or extra.get("n_model_calls") or 0)
    except Exception as e:
        row["note"] = f"honest fail: {type(e).__name__}: {str(e)[:90]}"
    row["submission"] = submission
    row["turns"] = turns
    row["wall_s"] = round(time.time() - t0, 1)
    # THE VERDICT: the court's own pytest AFTER the agent (the finish gate)
    try:
        v = env.execute({"command": "python -m pytest -q test_impl.py"}, timeout=120)
        resolved = v.get("returncode") == 0 and "passed" in (v.get("output") or "")
    except Exception:
        resolved = False
    row["resolved"] = resolved
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def run_beat(court_tasks=TASK_TURNS):
    rows = []
    for _ in range(court_tasks):
        t = generate_task()
        rows.append(run_task(t))
    n = sum(1 for r0 in rows if r0.get("resolved"))
    total_rows = resolved_all = 0
    try:
        for ln in open(LEDGER, encoding="utf-8-sig"):
            if '"resolved": true' in ln:
                resolved_all += 1
            total_rows += 1
    except FileNotFoundError:
        pass
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "beat": court_tasks, "beat_resolved": n,
           "score_pct": round(100 * resolved_all / max(1, total_rows), 1),
           "rows_total": total_rows, "rows": rows}
    print(f"[swe-smoke]: beat {n}/{court_tasks} resolved | cumulative "
          f"{doc['score_pct']}% over {total_rows} drill(s) | horizon-s: "
          f"{[r0.get('wall_s') for r0 in rows]}")
    return doc


if __name__ == "__main__":
    run_beat()