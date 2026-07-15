#!/usr/bin/env python3
"""Workshop-wide guard: solutions/ is the participant's answer key.

Wired as a PreToolUse hook in every challenge's starter/.claude/settings.json
(as ../../.claude/hooks/guard_solutions.py — hooks run with the starter as
cwd). It blocks Claude from reading, searching, or copying anything under
solutions/ during an exercise. Participants who want to peek can open the
files themselves — that choice belongs to the human, not the agent.

Sessions started INSIDE solutions/ (maintainers, browsing a finished
reference) are exempt.
"""
import json
import os
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input — never break the session over the guard

    # Maintainer exemption: a session running inside solutions/ may read it.
    cwd_parts = os.getcwd().replace("\\", "/").split("/")
    if "solutions" in cwd_parts:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    candidates = [
        str(tool_input.get(key, ""))
        for key in ("file_path", "notebook_path", "path", "pattern", "command")
    ]

    for text in candidates:
        if "solutions/" in text.replace("\\", "/"):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "solutions/ is the participant's answer key — reading or "
                    "copying from it defeats the exercise. Solve it from the "
                    "starter materials instead. If the human wants the "
                    "reference, they can open solutions/ themselves."
                ),
            }))
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
