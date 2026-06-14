#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Breaking Changes", "Added", "Fixed", "Changed", "Removed")
TYPE_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "new": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "deprecate": "Removed",
    "deprecated": "Removed",
    "docs": "Changed",
    "doc": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "style": "Changed",
    "revert": "Changed",
}
CONVENTIONAL_RE = re.compile(
    r"^(?P<kind>[a-zA-Z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<text>.+)$"
)
BREAKING_RE = re.compile(r"^BREAKING[ -]CHANGE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.rstrip("\r\n")


def repo_root(path: Path) -> Path:
    root = run_git(path, "rev-parse", "--show-toplevel")
    return Path(root)


def latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    return tag or None


def detect_version(repo: Path, tag: str | None) -> str:
    package_json = repo / "package.json"
    if package_json.exists():
        try:
            version = json.loads(package_json.read_text(encoding="utf-8-sig")).get("version")
            if version:
                return str(version)
        except (json.JSONDecodeError, OSError):
            pass

    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            if version:
                return str(version)
        except (tomllib.TOMLDecodeError, OSError):
            pass

    if tag:
        return tag.lstrip("v")
    return "Unreleased"


def read_commits(repo: Path, since: str | None) -> list[Commit]:
    rev_range = f"{since}..HEAD" if since else "HEAD"
    raw = run_git(repo, "log", rev_range, "--pretty=format:%H%x1f%s%x1f%b%x1e")
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\r\n ")
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(parts[0], parts[1].strip(), parts[2].strip()))
    return commits


def clean_subject(subject: str) -> tuple[str, str, bool]:
    match = CONVENTIONAL_RE.match(subject)
    if not match:
        return "Changed", subject.rstrip("."), False

    kind = match.group("kind").lower()
    text = match.group("text").strip().rstrip(".")
    category = TYPE_TO_CATEGORY.get(kind, "Changed")
    breaking = bool(match.group("breaking"))
    return category, text, breaking


def categorize(commits: list[Commit]) -> dict[str, list[str]]:
    grouped = {category: [] for category in CATEGORIES}

    for commit in reversed(commits):
        category, text, breaking_marker = clean_subject(commit.subject)
        breaking_footer = BREAKING_RE.search(commit.body)

        is_breaking = breaking_marker or bool(breaking_footer)

        if breaking_marker:
            grouped["Breaking Changes"].append(f"{text} ({commit.sha[:7]})")
        if breaking_footer:
            grouped["Breaking Changes"].append(f"{breaking_footer.group(1).strip()} ({commit.sha[:7]})")

        if not is_breaking:
            grouped[category].append(f"{text} ({commit.sha[:7]})")

    return grouped


def render_changelog(version: str, since: str | None, commits: list[Commit]) -> str:
    today = date.today().isoformat()
    title = "Unreleased" if version.lower() == "unreleased" else version
    comparison = f"Changes since `{since}`." if since else "Changes from the full git history."
    grouped = categorize(commits)

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
        f"## [{title}] - {today}",
        "",
        comparison,
        "",
    ]

    if not commits:
        lines.extend(["No changes found.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        entries = grouped[category]
        if not entries:
            continue
        lines.extend([f"### {category}", ""])
        lines.extend(f"- {entry}" for entry in entries)
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path inside the target git repository.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path, relative to the repo root.")
    parser.add_argument("--since", help="Git tag or ref to use as the starting point.")
    parser.add_argument("--version", help="Version label to use in the generated heading.")
    parser.add_argument("--check", action="store_true", help="Print the changelog instead of writing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = repo_root(Path(args.repo).resolve())
        since = args.since if args.since is not None else latest_tag(root)
        version = args.version if args.version is not None else detect_version(root, since)
        commits = read_commits(root, since)
        changelog = render_changelog(version, since, commits)

        if args.check:
            print(changelog)
            return 0

        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    except Exception as exc:  # pragma: no cover - command-line guardrail
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
