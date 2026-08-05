#!/usr/bin/env python3
"""PostToolUse hook: when a *structural* file of the vocab pipeline is edited
(the build/extract scripts or a template), remind Claude to check whether the
skill / commands / hooks that document them need updating — and to ASK the user
before changing any of those AI-config files.

Fires only for pipeline internals, not routine data files (known.md, learning.json).
"""
import json, sys

# Substrings that mark a "structured change" worth a docs/AI-config review.
TRIGGERS = (
    ".claude/skills/vocab-deck/scripts/",   # build.py, extract.py
    "templates/",                            # vocab.html template
)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = (data.get("tool_input", {}) or {}).get("file_path", "") or ""
if not any(t in path for t in TRIGGERS):
    sys.exit(0)   # not a structural change — stay silent

msg = (
    "Structured change detected in `%s`. Before finishing this turn, check whether "
    "the vocab-deck skill (SKILL.md), any slash command, or any hook still matches "
    "this change. If an update to a skill / command / hook is needed, ASK the user "
    "for approval and describe the change BEFORE editing any of those AI-config files."
) % path

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg,
    }
}))
