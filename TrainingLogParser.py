"""
TRAINING OBJECTIVE #3 (human-assigned): implement a log parser in this file.

Implement parse_log_line(line) and parse_log(text) satisfying:
  - lines look like: "2026-10-31 12:00:00 [INFO] message here"
  - parse_log_line returns dict(timestamp=str, level=str, message=str)
  - a malformed line returns {"error": "malformed", "raw": line}
  - parse_log(text) returns a list of parsed results (one per line)
  - levels are validated against INFO/WARN/ERROR/DEBUG (anything else malformed)

Current state: intentionally incomplete - Apex, apply the full pipeline.
"""

import re

_LOG_PATTERN = None  # TODO: define the regex per the objective

def parse_log_line(line):
    raise NotImplementedError("training objective - implement me")

def parse_log(text):
    raise NotImplementedError("training objective - implement me")