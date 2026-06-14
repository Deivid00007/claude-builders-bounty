# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

---

## Generate Changelog Skill

This repository includes `generate-changelog`, a Claude Code skill plus `bash changelog.sh` wrapper for creating a structured `CHANGELOG.md` from git history.

### Setup

1. Copy `generate-changelog/` and `changelog.sh` into the target repository.
2. From the target repository root, run `bash changelog.sh` or `python generate-changelog/scripts/generate_changelog.py`.
3. Review and commit the generated `CHANGELOG.md`.

### What It Does

- Reads commits since the latest git tag, or the full history when no tag exists.
- Detects the displayed version from `package.json`, `pyproject.toml`, or the latest git tag.
- Groups entries into `Added`, `Fixed`, `Changed`, `Removed`, and `Breaking Changes`.
- Supports `--check`, `--since`, `--version`, `--repo`, and `--output` options.

See `sample-output.md` for an example generated from a real local git repository.
