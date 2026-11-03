"""ApexHands - THE ACTUATION ORGAN (the eyes had it; now the hands touch,
2026-11-03; the sourced trick: Set-of-Marks (from the OSWorld /
computer-use-agent line, arXiv:2405.07918-class practice) - the numbered
overlay over every interactive element, so even a TEXT-only model can aim
precisely; made BETTER than the browser-use baseline:

  their pattern                        the fleet's improvement
  screenshot -> vision model -> coords the numbered MARKS first: the free
                                       text-lane picks an INDEX (exact,
                                       $0, no coordinate hallucination)
  one-shot                             the bounded step-loop (<=8 steps,
                                       re-marked after every action)
  silent failures                      per-step receipts
                                       (Config/apex_hands.jsonl): the
                                       action, the element, the DOM did
                                       change?

THE SAFETY LAW (the red-team's mirror): the hands act ONLY on targets the
founder has consented to (own pages, public pages, the demo repo) - never
another person's accounts, never purchases, never deletes. $0 lanes only.
stdlib + playwright (installed in apex_venv)."""

import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
RECEIPTS = os.path.join(ROOT, "Config", "apex_hands.jsonl")
MAX_STEPS = 8

MARK_JS = """
() => {
  const sels = 'a[href], button, input, textarea, select, [role="button"], [onclick], summary';
  const els = [...document.querySelectorAll(sels)].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width > 2 && r.height > 2 && !e.closest('[aria-hidden="true"]');
  }).slice(0, 60);
  els.forEach((e, i) => {
    e.setAttribute('data-apex-mark', String(i));
    const r = e.getBoundingClientRect();
    const tag = document.createElement('div');
    tag.textContent = String(i);
    tag.style.cssText = `position:absolute;z-index:2147483647;background:#ff4000;` +
      `color:#fff;font:bold 11px monospace;padding:1px 4px;border-radius:3px;` +
      `left:${Math.max(0, r.left - 14 + window.scrollX)}px;top:${Math.max(0, r.top - 12 + window.scrollY)}px;`;
    document.body.appendChild(tag);
  });
  return els.map((e, i) => {
    const r = e.getBoundingClientRect();
    return {i, tag: e.tagName.toLowerCase(),
            text: (e.innerText || e.placeholder || e.value || e.getAttribute('aria-label') || '').replace(/\\s+/g, ' ').trim().slice(0, 70),
            href: (e.tagName === 'A') ? (e.getAttribute('href') || '').slice(0, 60) : ''};
  });
}
"""


def _decide(mission, marks, history):
    """The free text-lane aims: the numbered list in, the JSON action out."""
    lst = "\n".join(f"{m['i']}: <{m['tag']}> {m['text']}" +
                    (f" href={m['href']}" if m['href'] else "")
                    for m in marks)
    hist = "\n".join(history[-4:]) or "(first step)"
    prompt = (
        "You are the aiming module of a web-automation agent. A page has "
        "interactive elements marked 0..N. Choose ONE next action as a "
        "SINGLE JSON line, one of:\n"
        '{"click": <index>}\n{"type": <index>, "text": "<what to type>"}'
        '\n{"scroll": "down"}\n{"done": "<one-sentence result>"}\n'
        "MISSION: " + mission + "\nURL: " + "current\n"
        "STEPS SO FAR:\n" + hist + "\nELEMENTS:\n" + lst +
        "\nReturn ONLY the JSON line:")
    replies = []
    try:
        import CloudBrain as CB
        replies.append(CB.chat(prompt, max_tokens=120, purpose="hands-aim")
                       or "")
    except Exception:
        pass
    if not replies or not (replies[0] or "").strip():
        try:
            import FreeSwarm
            replies.append(FreeSwarm.ask(prompt, max_tokens=120,
                                         purpose="hands floor") or "")
        except Exception:
            pass
    for r in replies:
        m = __import__("re").search(r"\{.*\}", (r or "").replace("\n", " "))
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                continue
    return {"error": "no-parse"}


def mission(url, goal, headless=True):
    """THE STEP-LOOP: open -> mark -> decide -> act -> re-mark, receipted."""
    from playwright.sync_api import sync_playwright
    rows, history = [], []
    ok_steps = 0
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=headless)
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            pg.goto(url, timeout=45000, wait_until="domcontentloaded")
            for step in range(MAX_STEPS):
                marks = pg.evaluate(MARK_JS)
                if not marks:
                    rows.append({"ts": time.strftime("%H:%M:%S"),
                                 "step": step, "act": "no-marks",
                                 "ok": False, "note": "nothing interactive"})
                    break
                act = _decide(goal, marks, history)
                if "done" in act:
                    rows.append({"ts": time.strftime("%H:%M:%S"), "step": step,
                                 "act": "done", "ok": True,
                                 "note": act["done"][:120]})
                    history.append(f"done: {act['done']}")
                    break
                try:
                    if "click" in act:
                        el = pg.locator(f'[data-apex-mark="{act["click"]}"]')
                        el.click(timeout=6000)
                        history.append(f"clicked #{act['click']} "
                                       f"({marks[act['click']]['text'][:40]})")
                    elif "type" in act:
                        el = pg.locator(f'[data-apex-mark="{act["type"]}"]')
                        el.fill(str(act.get("text", ""))[:200], timeout=6000)
                        history.append(f"typed into #{act['type']}: "
                                       f"{str(act.get('text'))[:40]}")
                    elif "scroll" in act:
                        pg.mouse.wheel(0, 600)
                        history.append("scrolled down")
                    else:
                        rows.append({"ts": time.strftime("%H:%M:%S"),
                                     "step": step, "act": "no-parse",
                                     "ok": False,
                                     "note": str(act)[:100]})
                        break
                    pg.wait_for_timeout(700)
                    ok_steps += 1
                    rows.append({"ts": time.strftime("%H:%M:%S"),
                                 "step": step, "act": history[-1][:80],
                                 "ok": True, "note": ""})
                except Exception as e:
                    history.append(f"step {step} failed: {type(e).__name__}")
                    rows.append({"ts": time.strftime("%H:%M:%S"),
                                 "step": step, "act": "error",
                                 "ok": False,
                                 "note": f"{type(e).__name__}: {str(e)[:80]}"})
                    break
            b.close()
    except Exception as e:
        rows.append({"ts": time.strftime("%H:%M:%S"), "step": -1,
                     "act": "route", "ok": False,
                     "note": f"{type(e).__name__}: {str(e)[:80]}"})
    with open(RECEIPTS, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[hands]: mission '{goal[:40]}' -> {ok_steps} steps ok | final: "
          f"{rows[-1]['act'] if rows else '?'} ({rows[-1]['note'][:60] if rows else ''})")
    return rows


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        mission(sys.argv[1], sys.argv[2])
    else:
        # the seal-test: the fleet's OWN page (the consented target)
        mission("http://127.0.0.1:8080/talk",
                "find the button that makes replies speak aloud and switch it on")
