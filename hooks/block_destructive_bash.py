#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RM_RF_RE = re.compile(r"(?<![\w-])rm\s+-(?:[^\s;|&]*r[^\s;|&]*f|[^\s;|&]*f[^\s;|&]*r)\b", re.IGNORECASE)
GIT_FORCE_PUSH_RE = re.compile(
    r"(?<![\w-])git\s+push\b(?=[^;&|]*(?:--force(?:-with-lease)?\b|-f\b))",
    re.IGNORECASE,
)
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def find_block_reason(command: str) -> str | None:
    checks = (
        (RM_RF_RE, "rm -rf can recursively delete files and directories."),
        (GIT_FORCE_PUSH_RE, "git push --force can overwrite remote history."),
        (DROP_TABLE_RE, "DROP TABLE can permanently remove database tables."),
        (TRUNCATE_RE, "TRUNCATE can permanently remove table data."),
    )
    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    delete_match = DELETE_FROM_RE.search(command)
    if delete_match:
        statement_tail = command[delete_match.end() :]
        statement_tail = re.split(r";|&&|\|\||\n", statement_tail, maxsplit=1)[0]
        if not WHERE_RE.search(statement_tail):
            return "DELETE FROM without a WHERE clause can remove every row in a table."

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    log_path = Path(os.environ.get("CLAUDE_HOOK_LOG", "~/.claude/hooks/blocked.log")).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked destructive Bash command: {reason}",
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = str(
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_blocked_attempt(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
