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

## Claude PR Reviewer Agent

This repository includes a Claude Code sub-agent plus CLI for reviewing GitHub pull requests and returning a structured Markdown comment.

### Setup

1. Copy `.claude/agents/pr-reviewer.md` into a Claude Code project.
2. Add `bin/` to your `PATH`, or run the script directly with `python scripts/claude_review.py`.
3. Review a PR:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The CLI fetches the PR diff, builds the sub-agent prompt, and invokes `claude --agent pr-reviewer -p` when the Claude CLI is available. If Claude is unavailable, it falls back to a deterministic local reviewer so CI and demos still produce the required structured Markdown.

### Output Format

Every review contains:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence`

### GitHub Action

`.github/workflows/claude-review.yml` runs the reviewer on pull requests and posts the generated Markdown comment with `gh pr comment`.

### Samples

Sample outputs for two real GitHub PRs are included under `samples/`.

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
