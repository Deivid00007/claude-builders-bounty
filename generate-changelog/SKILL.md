---
name: generate-changelog
description: Generate or refresh a structured CHANGELOG.md from a git repository's commit history. Use when the user asks for a changelog, release notes, Conventional Commit grouping, unreleased changes since the last tag, or a project version summary from package.json, pyproject.toml, or git tags.
---

# Generate Changelog

## Overview

Create a Keep a Changelog-style `CHANGELOG.md` from git history using Conventional Commit cues when available. Prefer the bundled Python generator for deterministic output, then review the result for project-specific wording before presenting it.

## Quick Start

From the repository root, run:

```bash
python generate-changelog/scripts/generate_changelog.py
```

Use `--check` in CI or review workflows to preview the generated changelog without writing it:

```bash
python generate-changelog/scripts/generate_changelog.py --check
```

## Workflow

1. Confirm the current directory is inside a git repository.
2. Run `scripts/generate_changelog.py` from the repository root or pass `--repo <path>`.
3. Review the generated sections, especially commit messages that did not follow Conventional Commits.
4. Commit the resulting `CHANGELOG.md` with the related release or documentation change.

## Categorization

The generator reads commits since the latest reachable git tag. If no tag exists, it reads the full history.

- `feat`, `add`, `new` -> `Added`
- `fix`, `bugfix`, `hotfix` -> `Fixed`
- `remove`, `delete`, `deprecate` -> `Removed`
- `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `style`, and uncategorized commits -> `Changed`
- `!` markers or `BREAKING CHANGE:` footers -> `Breaking Changes`

The heading uses the detected version from `package.json`, `pyproject.toml`, or the latest git tag. Unreleased changes are labeled `Unreleased`.

## Options

- `--output CHANGELOG.md`: choose a different output file.
- `--repo .`: generate from a different repository path.
- `--since <tag-or-ref>`: override the latest tag detection.
- `--version <name>`: override version detection.
- `--check`: print to stdout without writing the file.

## Script

Use `scripts/generate_changelog.py` for the actual changelog generation. It only depends on Python's standard library and the `git` CLI.
