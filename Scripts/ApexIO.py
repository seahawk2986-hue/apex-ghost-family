"""ApexIO - THE SPINE (2026-11-04): one parser, one writer, honest locks.

THE WEAKNESS IT KILLS: three hand-rolled .env schemas (ApexShard.env,
CloudBrain.env_keys, LaneGuard.env_load) could drift; six zero-byte .lock
files were unlocked-but-never-deleted; a mere file's existence could fake
liveness. The spine = the ONE contract every organ delegates to:

  env(repo=None)       the .env parser (utf-8-sig, comments, quotes)
  atom(path, data)     atomic write via tmp + os.replace (json or bytes)
  jload(path, def_)    tolerant json read
  lock(path, owner)    context-manager file lock that DELETES its zero-byte
                       lockfile on release (the litter class dies here)

Nothing existing breaks: the old function names keep their signatures and
delegate to the spine today; the spine carries the receipt comment.
$0, stdlib-only.
"""
import json
import os
import time


def env(repo=None):
    """THE .env parser (utf-8-sig + BOM + inline comments + quote strip)."""
    e = {}
    p = os.path.join(repo, ".env") if repo else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        for ln in open(p, encoding="utf-8-sig"):
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            v = v.split(" #", 1)[0].strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            e[k.strip()] = v
    except FileNotFoundError:
        pass
    return e


def jload(path, def_=None):
    try:
        return json.load(open(path, encoding="utf-8-sig"))
    except Exception:
        return def_


def atom(path, data):
    """Atomic write: tmp + os.replace; json-serializes dicts/lists."""
    tmp = path + ".tmp"
    if isinstance(data, (dict, list)):
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    else:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
    os.replace(tmp, path)


def lock(path, owner="apex"):
    """Context-manager exclusive lock; the zero-byte file is DELETED on
    release (the audited litter: SkillLibrary-style unlocks left every
    .lock behind forever). Cross-process via msvcrt byte-lock; a crash
    releases the OS handle (and a subsequent open re-creates the file)."""
    import msvcrt

    class _Lock:
        def __enter__(self):
            self.f = open(path + ".lock", "w")
            deadline = time.time() + 20
            while True:
                try:
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() > deadline:
                        raise TimeoutError(f"lock busy: {path}")
                    time.sleep(0.2)
            self.f.write(owner + "\n")
            self.f.flush()
            return self.f

        def __exit__(self, *exc):
            try:
                self.f.seek(0)          # unlock the SAME byte range that was
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                self.f.close()
                try:
                    os.remove(self.f.name)
                except OSError:
                    pass
            return False

    return _Lock()