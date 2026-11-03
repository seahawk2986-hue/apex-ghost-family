"""AnswerNorm - THE SHARED TRUTH-NORMALIZER (2026-11-04, GI round).

THE MEASURED BUG: the two most objective GI families scored 0% on exact-
match grading while the Court's value-aware grader scored the same minds
~40% on the same drills - the difference was not intelligence, it was
string-brittleness: 'Hello, World!' vs 'hello, world!' vs '"hello" vs
'Output: hello' all graded MISS. A grader that punishes quoting style is
measuring format compliance, not cognition.

THE NORM (deterministic, order-stable, no model calls):
  1. take the raw answer strip; drop a trailing period/space;
  2. peel wrapping quotes (paired ' " ` or a trailing fence);
  3. peel a leading label ("Answer:", "Output:", "The output is", etc.);
  4. peel a trailing confidence tail ("| confidence: high");
  5. collapse internal whitespace runs (keep case for strings);
  6. for NUMERIC comparisons: match by parsed value (float tolerance 1e-9);
  7. case-INSENSITIVE comparison fallback for string truths (the court
     already grades flaw-names by containment; the norm keeps that).
Sources: the family's measured A/B (the gym 0% vs the court 40.7% on
equivalent minds); Xiong et al., "Can LLMs Explicitly Express Their
Uncertainty?" arXiv:2306.13063 (2023) - the calibration-verbalization
standard this organ's cleaner rows feed; the family's own evidence-first
law (verify-or-unclaimed).
$0, stdlib-only, ~1ms per call.
"""
import re

_LABELS = ("answer", "output", "result", "the answer", "the output",
           "it prints", "prints", "returns", "return")
_CONF_RE = re.compile(r"\|\s*confidence:.*$", re.I)
_FENCE_RE = re.compile(r"^`+|`+$")


def norm(a):
    a = (a or "").strip()
    a = _CONF_RE.sub("", a).strip()
    a = _FENCE_RE.sub("", a).strip()
    # THE UNIFIED PEEL (2026-11-04 fix): labels and quotes interleave in
    # real answers ("Output: '10.5822'" = label AROUND quote AROUND value)
    # - peel alternatingly until NOTHING peels anymore (stable state).
    for _ in range(8):
        before = a
        for lab in _LABELS:
            low = a.lower()
            if low.startswith(lab + ":"):
                a = a[len(lab) + 1:].strip()
            elif low.startswith(lab + " is "):        # " is " = 4 chars
                a = a[len(lab) + 4:].strip()
        if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'`":
            a = a[1:-1].strip()
        if a and a[-1] in ".。":
            a = a[:-1].rstrip()
        if a == before:
            break
    a = re.sub(r"\s+", " ", a)
    return a


def is_num(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def match(answer, want):
    """The graded comparison: numeric truths compare by VALUE; string
    truths compare case-insensitively on the normalized forms; empty
    answers never match."""
    an, wn = norm(str(answer)), norm(str(want))
    if not an:
        return False
    if is_num(an) and is_num(wn):
        return abs(float(an) - float(wn)) < 1e-9
    return an.lower() == wn.lower()


if __name__ == "__main__":
    cases = [
        ('"Hello, World!"', "Hello, World!", True),
        ("hello, world.", "hello", False),   # different strings stay different
        ("hello", "hello", True),
        ("Output: '10.582'", "10.5822", False),  # values differ -> miss stands
        ("Output: '10.5822'", "10.5822", True),
        ("93.47200000000014", "93.47200000000014", True),
        ("The answer is 42 | confidence: high", "42", True),
        ("`ok`", "ok", True),
        ("", "42", False),
        ("Output: \"Hello, World!\"", "Hello, World!", True),
    ]
    for a, w, exp in cases:
        got = match(a, w)
        print(("PASS" if got == exp else "FAIL"), "|", repr(a[:34]), "vs",
              repr(w[:24]), "->", got)
    print("AnswerNorm selftest done")