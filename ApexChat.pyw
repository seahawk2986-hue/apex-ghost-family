"""APEX Chat v2 - native desktop window (pywebview) for the private console.

Uses Windows' built-in Edge WebView2 (no Electron, ~0 overhead). If pywebview
is unavailable, falls back to the default browser; if that fails as well, the
tkinter console class in ApexChatLegacy.pyw still works standalone.
"""

import base64
import os
import subprocess
import sys
import webbrowser

URL = "http://127.0.0.1:8080/talk"


def _ps_b64(command):
    """Run a PowerShell command via EncodedCommand (quoting-proof)."""
    enc = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    r = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", enc],
                       capture_output=True, text=True, timeout=10)
    return r.stdout or ""


class Api:
    """Native clipboard bridge for the chat page (pywebview js_api)."""

    def paste_clipboard(self):
        return _ps_b64("Get-Clipboard").strip()[:8000]

    def copy_to_clipboard(self, text):
        t = str(text or "")[:16000].replace('"', '`"')
        _ps_b64(f"Set-Clipboard -Value \"{t}\"")
        return True


def main():
    try:
        import webview
        webview.create_window("APEX — Private Console", URL,
                              width=880, height=660, min_size=(560, 420),
                              background_color="#0d1117", js_api=Api())
        webview.start()
        return
    except ImportError:
        pass
    except Exception as e:
        print("webview failed, opening browser:", e, file=sys.stderr)
    webbrowser.open(URL)


if __name__ == "__main__":
    main()