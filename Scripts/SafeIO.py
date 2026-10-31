"""SafeIO: the family's single write authority - atomic + locked everywhere."""
import json
import msvcrt
import os
import time

def _lock(path):
    lf = open(path + ".lock", "w")
    dl = time.time() + 30
    while True:
        try:
            msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
            return lf
        except OSError:
            if time.time() > dl:
                lf.close()
                return None
            time.sleep(0.08)


def write_json(path, data, indent=1):
    lf = _lock(path)
    if lf is None:
        return False
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        os.replace(tmp, path)
        return True
    finally:
        msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
        lf.close()


def read_json(path, default=None, encoding="utf-8-sig"):
    try:
        with open(path, encoding=encoding) as f:
            return json.load(f)
    except Exception:
        return default
