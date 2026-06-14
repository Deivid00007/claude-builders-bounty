from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"


REQUIRED_SECTIONS = [
    "## Stack & Versions",
    "## Dev Commands",
    "## Folder Structure",
    "## Naming Conventions",
    "## SQL & Migration Conventions",
    "## Component Patterns",
    "## Anti-Patterns To Avoid",
]

REQUIRED_TERMS = [
    "Next.js 15",
    "SQLite",
    "better-sqlite3",
    "Turso",
    "Drizzle",
    "pnpm dev",
    "pnpm db:migrate",
    "Server Components",
    "Server Actions",
    "organization_id",
    "Never edit an applied migration",
    "Do not put `use client`",
]


def test_required_sections_present():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    assert not missing, f"Missing sections: {missing}"


def test_required_terms_present():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    missing = [term for term in REQUIRED_TERMS if term not in text]
    assert not missing, f"Missing terms: {missing}"


def test_rules_are_opinionated_with_reasons():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    reason_count = text.lower().count("because ")
    assert reason_count >= 30, f"Expected at least 30 explicit reasons, found {reason_count}"


if __name__ == "__main__":
    test_required_sections_present()
    test_required_terms_present()
    test_rules_are_opinionated_with_reasons()
    print("CLAUDE.md template validation passed")
