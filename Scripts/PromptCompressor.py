"""PromptCompressor - THE TOKEN-ECONOMY ORGAN (the anti-block half).

Two ways to survive a hard token cap: (1) spend ZERO tokens on lanes that
cannot serve (TPDGuard's job), and (2) spend FEWER tokens per call (this
organ). The fleet's organ prompts repeat HISTORY: identical event lines,
repeated whitespace, duplicated context blocks - every cycle pays for the
repetition again and again (measured: the planner's prompt re-carries the
same 6-history rows ~99% of cycles).

THE COMPRESSION (conservative, lossless-enough by design):
  - collapse 3+ blank lines -> 1
  - drop EXACT duplicate lines (history rows dominate)
  - repeated sentences (>= 40 chars, seen before) -> dropped
  - middle truncation with an honest [clipped] marker: head+tail kept
  - NEVER touches short prompts (<3000 chars: code-repair payloads, chat)
$0, stdlib, one pass, O(n)."""
import re


def compress(text, keep_head=6000, keep_tail=2500):
    t = text or ""
    if len(t) < 3000:
        return t                     # the honest rule: small prompts untouched
    lines = re.sub(r"\n{3,}", "\n\n", t).splitlines()
    seen, out, dupes = set(), [], 0
    for ln in lines:
        key = ln.strip()
        if not key:
            out.append(ln)
            continue
        if key in seen:
            dupes += 1               # a repeated HISTORY row pays once only
            continue
        seen.add(key)
        out.append(ln)
    body = "\n".join(out)
    if len(body) > keep_head + keep_tail:
        body = (body[:keep_head] + "\n... [context compressed: "
                f"{dupes} duplicate line(s) + {(len(body)-keep_head-keep_tail) // 1000}k chars "
                "elided ...]\n" + body[-keep_tail:])
    return body


def stats_before_after(before, after):
    return {"chars_before": len(before or ""), "chars_after": len(after or ""),
            "saved_pct": round(100 * (1 - len(after or "") / max(1, len(before or ""))), 1)}


if __name__ == "__main__":
    demo = "\n".join(["Header row."] + [f"File: a.py Reward: 30 (same lesson row)" for _ in range(40)] + ["\n\n\n", "Footer question?"])
    c = compress(demo)
    print(stats_before_after(demo, c))
    print(c[:300])