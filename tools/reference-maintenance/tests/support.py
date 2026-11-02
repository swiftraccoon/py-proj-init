# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Local fixtures; never use user credentials or external network."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from reference_maintenance.model import Source

# unittest discovery uses this maintenance directory as its top level.
TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[1]


def git(*args: str, cwd: Path) -> str:
    """Run local fixture Git commands independently of user configuration."""
    environment = os.environ.copy()
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="Reference tests",
        GIT_AUTHOR_EMAIL="test@example.invalid",
        GIT_COMMITTER_NAME="Reference tests",
        GIT_COMMITTER_EMAIL="test@example.invalid",
    )
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        environment.pop(name, None)
    executable = shutil.which("git")
    if executable is None:
        message = "Git is required for local integration tests"
        raise FileNotFoundError(message)
    result = subprocess.run(  # noqa: S603 -- local fixtures; no shell
        [executable, "-c", "core.fsmonitor=false", *args],
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def upstream(parent: Path) -> tuple[Path, Source]:
    """Create a disposable upstream with byte-sensitive guide and license files."""
    source = parent / "upstream"
    source.mkdir()
    git("init", "--initial-branch=main", cwd=source)
    (source / "guide.md").write_bytes(b"Original guide\r\n")
    (source / "LICENSE").write_text("Fixture license\n", encoding="utf-8")
    (source / ".gitattributes").write_text("guide.md export-ignore\n", encoding="utf-8")
    git("add", "--all", cwd=source)
    git("-c", "core.autocrlf=false", "commit", "-m", "initial", cwd=source)
    config = Source(
        kind="git", url=str(source), license="Fixture license", branch="main"
    )
    return source, config
