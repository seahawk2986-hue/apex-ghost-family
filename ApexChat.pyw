"""APEX - Private Console (desktop chat client).

Native tkinter client for Apex's private channel (zero dependencies, ~25MB RAM).
Talks to http://127.0.0.1:8080/talk/api. If the channel is down, the watchdog
keeps the stack alive - just retry in a minute. Shows the memories Apex recalls
for each message (toggleable). Conversation history is stored in Apex's
episodic memory, not on disk here.
"""

import json
import queue
import threading
import tkinter as tk
import urllib.request
from tkinter.scrolledtext import ScrolledText

API = "http://127.0.0.1:8080/talk/api"
BG, FG, YOU, SYS, INPUT = "#0d1117", "#7ee787", "#58a6ff", "#8b949e", "#161b22"

TRAINING_DIRECTIVE = (
    "Apex, tonight you proved your reasoning is your weakest measured dimension - "
    "and I want that fixed properly. I'm not asking for a verbal promise: run your "
    "forecast gym on the hard half of the pool, log every prediction into calibration, "
    "write lessons for every miss, and show me your accuracy on the dashboard reasoning "
    "panel. Train your thinking the way you train your code: spec first, evidence after, "
    "honest numbers only. Also review your own Socratic verdicts - I want your shrink "
    "decisions justified in your own words, not rubber-stamped."
)


def now():
    import time
    return time.strftime("%H:%M:%S")


class ApexChat:
    def __init__(self):
        self.q = queue.Queue()
        self.win = tk.Tk()
        self.win.title("APEX - Private Console")
        self.win.geometry("820x580")
        self.win.configure(bg=BG)
        self.win.minsize(560, 420)

        header = tk.Label(self.win, text="APEX PRIVATE CONSOLE",
                          bg=BG, fg="#58a6ff", font=("Consolas", 13, "bold"))
        header.pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(self.win, text="direct channel - conversations live in Apex's episodic memory",
                 bg=BG, fg=SYS, font=("Consolas", 8)).pack(anchor="w", padx=12, pady=(0, 6))

        self.log = ScrolledText(self.win, bg=BG, fg=FG, wrap="word", state="disabled",
                                font=("Consolas", 10), relief="flat", borderwidth=0)
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        for tag, color in (("you", YOU), ("apex", FG), ("sys", SYS), ("mem", SYS)):
            self.log.tag_configure(tag, foreground=color)
        self.log.tag_configure("stamp", foreground=SYS, font=("Consolas", 7))

        row = tk.Frame(self.win, bg=BG)
        row.pack(fill="x", padx=10, pady=(0, 10))
        self.entry = tk.Entry(row, bg=INPUT, fg="#e6edf3", insertbackground=FG,
                              relief="flat", font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.entry.bind("<Return>", lambda _e: self.send())
        self.entry.focus()
        tk.Button(row, text="SEND", command=self.send, bg="#238636", fg="white",
                  relief="flat", padx=16, activebackground="#2ea043",
                  font=("Consolas", 10, "bold")).pack(side="left", padx=(8, 0))
        tk.Button(row, text="📋 directive", command=self.load_directive,
                  bg="#30363d", fg="#e6edf3", relief="flat", padx=10,
                  activebackground="#484f58").pack(side="left", padx=(6, 0))
        self.show_mem = tk.BooleanVar(value=True)
        tk.Checkbutton(row, text="recalled memory", variable=self.show_mem, bg=BG, fg=SYS,
                       selectcolor=INPUT, activebackground=BG, relief="flat").pack(side="left", padx=(10, 0))

        self.add("sys", "Private channel to Apex. He remembers this conversation. "
                        "Type 'remember this ...' to write a permanent lesson.")
        threading.Thread(target=self._load_notes, daemon=True).start()
        self.win.after(120, self.pump)
        self.win.mainloop()

    def _load_notes(self):
        """Apex's overnight dream notes greet you first."""
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/notes", timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
            for n in (data.get("notes") or [])[-1:]:
                self.q.put(("sys", f"[{n.get('ts')}] APEX (overnight dream): {n.get('note', '')[:200]}"))
        except Exception:
            pass

    def add(self, tag, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{now()}] ", ("stamp",))
        self.log.insert("end", text + "\n\n", (tag,))
        self.log.see("end")
        self.log.configure(state="disabled")

    def load_directive(self):
        """Drop the training directive into the input box, ready to send."""
        self.entry.delete(0, "end")
        self.entry.insert(0, TRAINING_DIRECTIVE)
        self.entry.focus()

    def send(self):
        t = self.entry.get().strip()
        if not t:
            return
        self.entry.delete(0, "end")
        self.add("you", f"YOU: {t}")
        self.add("apex", "APEX: thinking...")
        threading.Thread(target=self._ask, args=(t,), daemon=True).start()

    def _ask(self, t):
        try:
            req = urllib.request.Request(
                API, data=json.dumps({"message": t}).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=170) as r:
                data = json.loads(r.read().decode("utf-8"))
            reply = data.get("reply") or "(empty response)"
            self.q.put(("apex", f"APEX: {reply}"))
            if self.show_mem.get():
                for x in (data.get("recall") or [])[:3]:
                    self.q.put(("mem", f"   recalled: {x.get('text', '')[:110]}"))
        except Exception:
            self.q.put(("sys", "APEX: channel down - watchdog is keeping the stack alive. "
                               "Give it a minute and try again."))

    def pump(self):
        try:
            while True:
                tag, text = self.q.get_nowait()
                self.add(tag, text)
        except queue.Empty:
            pass
        self.win.after(150, self.pump)


if __name__ == "__main__":
    ApexChat()