"""APEX Chat v2 - native desktop window (pywebview) for the private console.

Uses Windows' built-in Edge WebView2 (no Electron, ~0 overhead). If pywebview
is unavailable, falls back to the default browser; if that fails as well, the
tkinter console class in ApexChatLegacy.pyw still works standalone.
"""

import os
import sys
import webbrowser

URL = "http://127.0.0.1:8080/talk"


def main():
    try:
        import webview
        webview.create_window("APEX — Private Console", URL,
                              width=880, height=660, min_size=(560, 420),
                              background_color="#0d1117")
        webview.start()
        return
    except ImportError:
        pass
    except Exception as e:
        print("webview failed, opening browser:", e, file=sys.stderr)
    webbrowser.open(URL)


if __name__ == "__main__":
    main()