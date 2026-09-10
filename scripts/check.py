#!/usr/bin/env python3
"""Validate Markdown structure, local links, and public identity policy."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = sorted(ROOT.rglob("*.md"))
ERRORS: list[str] = []


def validate_markdown(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)

    if content.count("```") % 2:
        ERRORS.append(f"{relative}: unmatched fenced code block")

    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean_target = target.split("#", 1)[0]
        if clean_target and not (path.parent / clean_target).resolve().exists():
            ERRORS.append(f"{relative}: missing local link target {target}")


for markdown_file in MARKDOWN_FILES:
    validate_markdown(markdown_file)

all_text = "\n".join(path.read_text(encoding="utf-8") for path in MARKDOWN_FILES).lower()
for forbidden in ("mamu" + "duri", "jeevanm.aws" + "@gmail.com"):
    if forbidden in all_text:
        ERRORS.append("Repository contains a disallowed personal identity value")

if ERRORS:
    print("Validation failed:", file=sys.stderr)
    for error in ERRORS:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"Validation passed for {len(MARKDOWN_FILES)} Markdown files.")
