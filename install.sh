#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
HOOK_DIR="$CLAUDE_DIR/hooks"
HOOK_TARGET="$HOOK_DIR/block_destructive_bash.py"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

mkdir -p "$HOOK_DIR"
cp "$ROOT/hooks/block_destructive_bash.py" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
  PYTHON_BIN=(python3)
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
  PYTHON_BIN=(python)
elif command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
  PYTHON_BIN=(py -3)
else
  echo "error: Python 3 is required to install the hook" >&2
  exit 1
fi

"${PYTHON_BIN[@]}" - "$SETTINGS_FILE" "$HOOK_TARGET" <<'PY'
import json
import sys
from pathlib import Path

settings_file = Path(sys.argv[1]).expanduser()
hook_target = Path(sys.argv[2]).expanduser()
settings_file.parent.mkdir(parents=True, exist_ok=True)

if settings_file.exists():
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"Refusing to edit invalid JSON: {settings_file}")
else:
    settings = {}

entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(hook_target),
            "args": [],
        }
    ],
}

pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
already_installed = any(
    group.get("matcher") == "Bash"
    and any(hook.get("command") == str(hook_target) for hook in group.get("hooks", []))
    for group in pre_tool_use
)
if not already_installed:
    pre_tool_use.append(entry)

settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed {hook_target}")
print(f"Updated {settings_file}")
PY
