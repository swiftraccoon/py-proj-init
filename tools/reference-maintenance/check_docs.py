#!/usr/bin/env -S uv run --script --locked
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.3,<9", "rich>=14,<15"]
# ///
# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Check local links in authored Markdown without building upstream websites."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

import click
from rich.console import Console

from reference_maintenance.cli import reference_root

if TYPE_CHECKING:
    from pathlib import Path


def check(root: Path) -> list[str]:
    """Return broken local file links, excluding links within code examples."""
    documents = [
        root / name for name in ("README.md", "AGENTS.md", "references/README.md")
    ]
    documents.extend(sorted((root / "docs").glob("*.md")))
    documents.extend(sorted((root / "tools/reference-maintenance").glob("*.md")))
    errors: list[str] = []
    for document in documents:
        text = document.read_text(encoding="utf-8")
        text = re.sub(
            r"^```[^\n]*\n.*?^```[^\n]*$", "", text, flags=re.MULTILINE | re.DOTALL
        )
        for match in re.finditer(r"\[[^\]\n]*\]\(([^)\s]+)\)", text):
            target = match.group(1)
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = document.parent / unquote(parsed.path)
            if not resolved.exists():
                errors.append(f"{document.relative_to(root)}: missing {target}")
    return errors


@click.command()
def main() -> None:
    """Report broken local links with a nonzero status for CI."""
    errors = check(reference_root())
    if errors:
        Console(stderr=True, markup=False).print("\n".join(errors), style="red")
        raise click.exceptions.Exit(1)
    Console().print("Authored Markdown local links are valid.", style="green")


if __name__ == "__main__":
    main()
