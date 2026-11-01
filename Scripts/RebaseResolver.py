"""THE REBASE-RESOLVER (the standing cure): the conflicts'
union-principle: the jsonl = the row-union (both true); the json = the
key-merge (both-kept); then the rebase --continue. Bounded + honest."""
import glob
import json
import os
import re
import subprocess
import sys


def union_jsonl(p):
    t = open(p, encoding="utf-8").read()
    seen, rows = set(), []
    for ln in t.splitlines():
        s = ln.strip()
        if not s or s.startswith(("<", "=", ">")):
            continue
        try:
            d = json.loads(s)
            k = json.dumps(d, sort_keys=True, ensure_ascii=False)[:180]
            if k in seen:
                continue
            seen.add(k)
            rows.append(s)
        except Exception:
            rows.append(s)
    open(p, "w", encoding="utf-8", newline="\n").write(
        "\n".join(rows) + "\n")
    return len(rows)


def merge_json(p, encoding="strict"):
    # the honest: parse the blocks; merge the keys; theirs = the freshest
    t = open(p, encoding="utf-8", errors=encoding if encoding != "strict"
             else None).read()

    def side(text, name):
        out = []
        take = name
        for ln in text.splitlines():
            if ln.startswith("<<<<<<<"):
                take = 0
                continue
            if ln.startswith("======="):
                take = 1
                continue
            if ln.startswith(">>>>>>>"):
                take = None
                continue
            if take is None:
                out.append(ln)
            else:
                out.append(ln if take else "") if False else None
                if take in (0, 1):
                    out.append(ln)
        return out

    # the simpler honest: parse the conflict-blocks; merge the top-level keys
    t = open(p, encoding="utf-8").read()
    blocks = re.split(r"^(<<<<<<<.*|=======|>>>>>>>.*)$", t, flags=re.M)
    base, ours, theirs = [], [], []
    mode = "base"
    for ln in t.splitlines():
        if ln.startswith("<<<<<<<"):
            mode = "ours"
            continue
        if ln.startswith("======="):
            mode = "theirs"
            continue
        if ln.startswith(">>>>>>>"):
            mode = None
            continue
        if mode == "base":
            base.append(ln)
        elif mode == "ours":
            ours.append(ln)
        elif mode == "theirs":
            theirs.append(ln)
    try:
        O = json.loads("\n".join(x for x in ours if x.strip()) or "{}")
        T = json.loads("\n".join(x for x in theirs if x.strip()) or "{}")
        B = json.loads("\n".join(x for x in base if x.strip()) or "{}")
        m = dict(B)
        m.update(O)
        m.update(T)  # theirs = the freshest (the runner's grain!)
        open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(m, ensure_ascii=False, indent=1))
        return "keys-merged"
    except Exception as e:
        # their side = the whole-truth fallback (the freshest grain)
        open(p, "w", encoding="utf-8", newline="\n").write(
            "\n".join(theirs if theirs else base))
        return f"theirs-fallback ({str(e)[:40]})"


def run():
    resolved = []
    for p in glob.glob(r"Config\**\*", recursive=True) + \
            glob.glob(r"Config\*.json"):
        if not os.path.isfile(p):
            continue
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue  # the unreadable = skip (the honest)
        if "<<<<<<<" in t:
            if p.endswith(".jsonl"):
                resolved.append((p, f"{union_jsonl(p)} rows"))
            else:
                resolved.append((p, merge_json(p, encoding="replace")))
            subprocess.run(["git", "add", p])
    print(f"[resolver] {resolved}")
    r = subprocess.run(["git", "-c", "core.editor=true", "rebase",
                        "--continue"], capture_output=True, text=True)
    print(f"[resolver] the continue: rc={r.returncode} "
          f"{(r.stdout or r.stderr).strip()[:120]}")


if __name__ == "__main__":
    run()