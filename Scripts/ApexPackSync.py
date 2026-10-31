"""ApexPackSync - autonomous pack maintenance (Sentry tick, drift-only).

Compares SHA256 of shipped engine files vs the last-sync record. On drift it
refreshes the supplemental pack's engine + rebuilds the delivery zip + Desktop
copies so shipped artifacts ALWAYS match the tested version. Honest + cheap."""
import hashlib
import json
import os
import shutil
import time
import zipfile

ADAPTER = r"C:\Users\seaha\Apex-Adapter"
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(ADAPTER, "pack_sync_state.json")
FILES = ("companion.py", "v2_job_engine.py", "v2_contract.py")


def _desktop():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        return winreg.QueryValueEx(k, "Desktop")[0]
    except Exception:
        return os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    hmap = {n: sha(os.path.join(ADAPTER, n)) for n in FILES}
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        st = {}
    if st.get("hashes") == hmap:
        return
    packp = os.path.join(ADAPTER, "Apex-V2-Supplemental-Pack.zip")
    try:
        with zipfile.ZipFile(packp) as z:
            pairs = [(n, z.read(n)) for n in z.namelist()]
    except Exception:
        return
    pairs = [(n, open(os.path.join(ADAPTER, n), "rb").read()
              if n in FILES else d) for n, d in pairs]
    with zipfile.ZipFile(packp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in pairs:
            z.writestr(n, d)
    with zipfile.ZipFile(os.path.join(ADAPTER, "Apex-V2-Completion-Pack.zip")) as z:
        comp = [(n, z.read(n)) for n in z.namelist()]
    cover = ""
    try:
        cover = open(os.path.join(REPO, "Logs", "mica_send2.txt"), encoding="utf-8").read()
    except Exception:
        pass
    out = os.path.join(_desktop(), "Apex-V2-Mica-Delivery.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("COVER-MESSAGE.txt", cover)
        for n, d in pairs:
            z.writestr("SUPPLEMENTAL/" + n, d)
        for n, d in comp:
            z.writestr("COMPLETION/" + n, d)
    shutil.copy2(out, os.path.join(ADAPTER, "Apex-V2-Mica-Delivery.zip"))
    micah = os.path.join(_desktop(), "Micah")
    os.makedirs(micah, exist_ok=True)
    shutil.copy2(out, os.path.join(micah, "Apex-V2-Mica-Delivery.zip"))
    st["hashes"] = hmap
    st["synced"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
