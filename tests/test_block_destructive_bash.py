import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, *, tool_name: str = "Bash"):
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "blocked.log"
        payload = {
            "session_id": "test",
            "cwd": "/tmp/example-project",
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "tool_use_id": "toolu_test",
        }
        env = os.environ.copy()
        env["CLAUDE_HOOK_LOG"] = str(log_path)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        return result, log_text


class BlockDestructiveBashTests(unittest.TestCase):
    def assert_blocked(self, command: str, expected_reason: str):
        result, log_text = run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertIn("permissionDecision", result.stdout)
        self.assertIn("deny", result.stdout)
        self.assertIn(expected_reason, result.stdout)
        log_entry = json.loads(log_text)
        self.assertEqual(log_entry["attempted_command"], command)
        self.assertEqual(log_entry["project_path"], "/tmp/example-project")
        self.assertIn("timestamp", log_entry)

    def assert_allowed(self, command: str):
        result, log_text = run_hook(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_text, "")

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf build/", "rm -rf")

    def test_blocks_drop_table(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_git_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")

    def test_blocks_truncate(self):
        self.assert_blocked('mysql -e "TRUNCATE TABLE sessions"', "TRUNCATE")

    def test_blocks_delete_without_where(self):
        self.assert_blocked('psql -c "DELETE FROM users"', "DELETE FROM without a WHERE")

    def test_allows_delete_with_where(self):
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')

    def test_allows_normal_bash(self):
        self.assert_allowed("npm test && git status")

    def test_ignores_non_bash_tool(self):
        result, log_text = run_hook("rm -rf build", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(log_text, "")


if __name__ == "__main__":
    unittest.main()
