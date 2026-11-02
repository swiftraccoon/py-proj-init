# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Export a verified pack while preserving the consuming project's own files."""

from __future__ import annotations

import logging
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import git, sync
from .model import OS_METADATA, read_manifest, require

PACK_NAME = ".python-reference"
REQUIRED_ENTRIES = (
    "README.md",
    "AGENTS.md",
    "LICENSE",
    ".gitattributes",
    "docs",
    "references",
    "templates",
    "tools/reference-maintenance",
)
OPTIONAL_ENTRIES = (".editorconfig", ".gitignore")
TOOL_ENTRIES = (
    "reference.py",
    "reference.py.lock",
    "check_docs.py",
    "check_docs.py.lock",
    "reference_maintenance",
    "tests",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
)
EXCLUDED = frozenset(
    {
        ".git",
        ".cache",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "htmlcov",
        "build",
        "dist",
        ".reference-maintenance.lock",
    }
)


@dataclass(frozen=True)
class Export:
    """Installed location and advisory Git-ignore findings."""

    destination: Path
    ignored_by_git: tuple[str, ...]


def _copy(source: Path, destination: Path, *, upstream: bool) -> None:
    mode = source.lstat().st_mode
    require(not stat.S_ISLNK(mode), f"Reference pack contains a symlink: {source}")
    if source.name in OS_METADATA:
        return
    if not upstream and (
        source.name in EXCLUDED
        or source.suffix in {".pyc", ".pyo"}
        or source.name.endswith(".egg-info")
    ):
        return
    if stat.S_ISDIR(mode):
        destination.mkdir()
        for child in sorted(source.iterdir()):
            _copy(child, destination / child.name, upstream=upstream)
    else:
        require(
            stat.S_ISREG(mode), f"Reference pack contains a nonregular file: {source}"
        )
        shutil.copyfile(source, destination)
        destination.chmod(mode & 0o777)


def _ignored(project: Path, paths: list[str]) -> tuple[str, ...]:
    try:
        result = git.run(
            ["check-ignore", "--no-index", "-z", "--stdin"],
            cwd=project,
            data=b"".join(f"{PACK_NAME}/{name}\0".encode() for name in paths),
        )
    except (OSError, TimeoutError):
        return ()
    # Advisory only: 1 means no ignored paths, 128 means no work tree.
    if result.returncode != 0:
        return ()
    return tuple(
        name.decode("utf-8", errors="replace")
        for name in result.stdout.split(b"\0")
        if name
    )


def run(root: Path, project: Path) -> Export:
    """Copy, verify, and install a complete pack into an existing project."""
    root = root.resolve(strict=True)
    project = project.resolve(strict=True)
    require(project.is_dir(), "Project path must be a directory")
    require(
        not project.is_relative_to(root),
        "Choose a project outside the reference workspace",
    )
    destination = project / PACK_NAME
    require(
        not (destination.exists() or destination.is_symlink()),
        f"Reference pack already exists; refusing to overwrite: {destination}",
    )
    for name in REQUIRED_ENTRIES:
        require((root / name).exists(), f"Incomplete reference pack; missing {name}")
    for name in TOOL_ENTRIES:
        require(
            (root / "tools/reference-maintenance" / name).exists(),
            f"Incomplete maintenance tool; missing {name}",
        )
    sources = read_manifest(root)
    require(bool(sources), "Fetch reference snapshots before exporting")
    sync.run(root, options=sync.Options(check=True), report=lambda _: None)
    with tempfile.TemporaryDirectory(
        prefix=".python-reference-export-", dir=project
    ) as temporary:
        staged = Path(temporary) / PACK_NAME
        staged.mkdir()
        for name in REQUIRED_ENTRIES + OPTIONAL_ENTRIES:
            source = root / name
            if source.exists() or source.is_symlink():
                target = staged / name
                target.parent.mkdir(parents=True, exist_ok=True)
                _copy(source, target, upstream=name == "references")
        sync.run(staged, options=sync.Options(check=True), report=lambda _: None)
        paths = sorted(
            path.relative_to(staged).as_posix()
            for path in staged.rglob("*")
            if path.is_file()
        )
        require(
            not (destination.exists() or destination.is_symlink()),
            f"Reference pack already exists; refusing to overwrite: {destination}",
        )
        staged.rename(destination)
    try:
        ignored = _ignored(project, paths)
    except (OSError, subprocess.SubprocessError) as exc:
        # Installation succeeded; a diagnostic-only check must not report that
        # the requested copy failed or attempt to roll it back.
        logging.getLogger(__name__).warning(
            "Pack installed, but Git ignore rules could not be checked: %s", exc
        )
        ignored = ()
    return Export(destination, ignored)
