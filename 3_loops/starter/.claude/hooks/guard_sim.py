#!/usr/bin/env python3
"""PreToolUse guard for Challenge 5: the world and the referee are frozen.

Blocks edits to the simulator, the checks, the ops database and the API
schema — through the file tools AND through mutating Bash commands (mv, cp,
rm, redirects), because an allowlisted `mv` is a write path too. Running the
frozen scripts (`python3 checks/...`) stays allowed. Python (not bash) so it
behaves the same on macOS, Linux and Windows. Wired up in
.claude/settings.json.
"""
import json
import re
import sys

FROZEN = (
    "depot_sim.py",
    "check_dashboard.py",
    "db_query.py",
    "guard_sim.py",
    "fleet_ops.db",
    "schema.sql",
)
FROZEN_RE = "|".join(re.escape(n) for n in FROZEN)


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_name = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {}) or {}

if tool_name == "Bash":
    command = str(tool_input.get("command", ""))
    mutating = re.search(
        rf"(?:^|[;&|]\s*)\s*(?:mv|cp|rm|dd|sed|tee|truncate)\b[^;&|]*\b({FROZEN_RE})",
        command,
    ) or re.search(rf">\s*\S*({FROZEN_RE})", command)
    if mutating:
        block(
            f"{mutating.group(1)} is part of the world/referee for this "
            "challenge and is frozen — commands may read or run it, never "
            "move, overwrite or delete it."
        )
    sys.exit(0)

path = str(tool_input.get("file_path", "") or tool_input.get("notebook_path", ""))
normalized = path.replace("\\", "/")
basename = normalized.rstrip("/").rsplit("/", 1)[-1]

# The dashboard is the participant's canvas — never frozen, whatever the name.
if "/dashboard/" in normalized:
    sys.exit(0)

in_checks_dir = normalized.startswith("checks/") or "/checks/" in normalized
if basename in FROZEN or in_checks_dir:
    what = basename if basename in FROZEN else "checks/"
    block(
        f"{what} is part of the world/referee for this challenge and is "
        "frozen — read it, never edit it. Fix the dashboard or your own "
        "artefacts (OPS_LOG.md, TRIAGE.md, live/ops_status.json) instead."
    )

sys.exit(0)
