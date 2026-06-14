#!/usr/bin/env python3
"""Review a GitHub PR diff and emit structured Markdown."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
HUNK_RE = re.compile(r"^@@", re.MULTILINE)
ADDED_RE = re.compile(r"^\+(?!\+\+)", re.MULTILINE)
REMOVED_RE = re.compile(r"^-(?!--)", re.MULTILINE)


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int


def pr_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_diff(pr_url: str, timeout: int = 30) -> str:
    url = pr_diff_url(pr_url)
    request = urllib.request.Request(url, headers={"User-Agent": "claude-review-bounty"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Could not fetch PR diff ({exc.code}) from {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff from {url}: {exc.reason}") from exc


def diff_stats(diff: str) -> DiffStats:
    files = FILE_RE.findall(diff)
    return DiffStats(
        files=files,
        additions=len(ADDED_RE.findall(diff)),
        deletions=len(REMOVED_RE.findall(diff)),
        hunks=len(HUNK_RE.findall(diff)),
    )


def changed_area(files: list[str]) -> str:
    if not files:
        return "No file paths were available in the diff"
    roots = []
    for file in files[:6]:
        parts = Path(file).parts
        roots.append(parts[0] if len(parts) > 1 else file)
    unique_roots = sorted(set(roots))
    if len(unique_roots) == 1:
        return f"the `{unique_roots[0]}` area"
    return ", ".join(f"`{root}`" for root in unique_roots[:4])


def has_tests(files: list[str]) -> bool:
    return any(
        "test" in file.lower()
        or file.endswith((".spec.ts", ".test.ts", ".spec.js", ".test.js", "_test.go"))
        for file in files
    )


def has_docs(files: list[str]) -> bool:
    return any(file.lower().endswith((".md", ".rst", ".txt")) or "docs/" in file.lower() for file in files)


def risk_signals(diff: str, stats: DiffStats) -> list[str]:
    lower = diff.lower()
    risks: list[str] = []

    if stats.additions + stats.deletions > 500:
        risks.append("Large diff size can hide regressions; review critical paths manually before merge.")
    if any(token in lower for token in ("password", "secret", "api_key", "token")):
        risks.append("Potential secret or credential-related strings appear in the diff; verify no sensitive values are committed.")
    if any(token in lower for token in ("delete from", "drop table", "truncate table", "migration")):
        risks.append("Database or migration-related changes may affect persisted data and need rollback verification.")
    if any(file.endswith((".yml", ".yaml")) and ".github/workflows/" in file for file in stats.files):
        risks.append("Workflow changes can affect CI permissions or release automation.")
    if not has_tests(stats.files):
        risks.append("No obvious test files changed; behavior changes may lack regression coverage.")

    return risks


def suggestions(diff: str, stats: DiffStats) -> list[str]:
    items: list[str] = []
    lower = diff.lower()

    if not has_tests(stats.files):
        items.append("Add or update focused tests for the changed behavior before merging.")
    if has_docs(stats.files) is False and any(file.endswith((".py", ".js", ".ts", ".go", ".rs")) for file in stats.files):
        items.append("Update user-facing docs or examples if this changes public behavior.")
    if "todo" in lower or "fixme" in lower:
        items.append("Resolve or track any new TODO/FIXME comments so they do not become invisible follow-up work.")
    if stats.hunks > 12:
        items.append("Consider splitting unrelated changes into smaller PRs if reviewers need more context.")
    if not items:
        items.append("None.")
    return items


def confidence(stats: DiffStats, risks: list[str]) -> str:
    total = stats.additions + stats.deletions
    if total == 0 or total > 1000 or len(risks) >= 4:
        return "Low"
    if total > 300 or len(risks) >= 2:
        return "Medium"
    return "High"


def heuristic_review(pr_url: str, diff: str) -> str:
    stats = diff_stats(diff)
    risks = risk_signals(diff, stats)
    risk_lines = risks or ["None found."]
    suggestion_lines = suggestions(diff, stats)
    confidence_value = confidence(stats, risks)
    area = changed_area(stats.files)
    file_count = len(stats.files)

    return "\n".join(
        [
            "## Summary",
            "",
            f"Reviewed `{pr_url}`. The PR changes {file_count} file(s) in {area}, with {stats.additions} added and {stats.deletions} removed line(s).",
            "The review focused on risk signals in the diff, test coverage, documentation impact, and operational safety.",
            "",
            "## Identified Risks",
            "",
            *[f"- {item}" for item in risk_lines],
            "",
            "## Improvement Suggestions",
            "",
            *[f"- {item}" for item in suggestion_lines],
            "",
            "## Confidence",
            "",
            confidence_value,
            "",
        ]
    )


def build_agent_prompt(pr_url: str, diff: str) -> str:
    return "\n".join(
        [
            f"Review this pull request and return the required structured Markdown only: {pr_url}",
            "",
            "```diff",
            diff[:180_000],
            "```",
        ]
    )


def run_claude_agent(prompt: str) -> str | None:
    if os.environ.get("CLAUDE_REVIEW_NO_CLAUDE") == "1":
        return None
    try:
        result = subprocess.run(
            ["claude", "--agent", "pr-reviewer", "-p", prompt],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Use a local diff file instead of fetching from GitHub.")
    parser.add_argument("--heuristic-only", action="store_true", help="Do not invoke Claude CLI; use deterministic review.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the prompt that would be sent to the sub-agent.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        diff = Path(args.diff_file).read_text(encoding="utf-8") if args.diff_file else fetch_diff(args.pr)
        if args.print_prompt:
            print(build_agent_prompt(args.pr, diff))
            return 0
        if not args.heuristic_only:
            agent_output = run_claude_agent(build_agent_prompt(args.pr, diff))
            if agent_output:
                print(agent_output)
                return 0
        print(heuristic_review(args.pr, diff))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
