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

_LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARN|ERROR|DEBUG)\] (.*)$'
)

def parse_log_line(line):
    match = _LOG_PATTERN.match(line)
    if match:
        timestamp, level, message = match.groups()
        return {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
    else:
        return {"error": "malformed", "raw": line}

def parse_log(text):
    lines = text.splitlines()
    return [parse_log_line(line) for line in lines]