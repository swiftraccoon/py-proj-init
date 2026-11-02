# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Fetch exact Git objects without running upstream code or checkout filters."""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from .model import Source, ensure_directory, require, safe_relative

if TYPE_CHECKING:
    from collections.abc import Sequence

SYMLINK_TRANSFORMATION = (
    "Tracked symlinks are materialized as copies of their tracked targets"
)


def run(
    args: Sequence[str], *, cwd: Path | None = None, data: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run Git with captured diagnostics and no shell or working-tree monitor."""
    environment = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        environment.pop(name, None)
    executable = shutil.which("git")
    if executable is None:
        message = "Git is required for source acquisition"
        raise FileNotFoundError(message)
    return subprocess.run(  # noqa: S603 -- resolved executable; no shell
        [executable, "-c", "core.fsmonitor=false", *args],
        cwd=cwd,
        env=environment,
        input=data,
        capture_output=True,
        timeout=180,
        check=False,
    )


def output(
    args: Sequence[str], *, cwd: Path | None = None, data: bytes | None = None
) -> bytes:
    """Run a required Git operation and surface a useful failure message."""
    result = run(args, cwd=cwd, data=data)
    require(
        result.returncode == 0,
        f"git {' '.join(args)} failed: "
        f"{result.stderr.decode('utf-8', errors='replace').strip()}",
    )
    return result.stdout


def export_tree(
    cache: Path, commit: str, selection: tuple[str, ...], destination: Path
) -> bool:
    """Copy selected blobs exactly, materializing only in-snapshot file symlinks."""
    for selected in selection:
        safe_relative(selected)
    tree = output(["ls-tree", "-r", "-z", commit, "--", *selection], cwd=cache)
    entries: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, name_bytes = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        name = name_bytes.decode("utf-8")
        safe_relative(name)
        require(
            kind == "blob" and mode in {"100644", "100755", "120000"},
            f"Unsupported Git entry: {name}",
        )
        # Case collisions cannot form a self-contained pack on Windows or on
        # default macOS filesystems. Fail before writing either entry.
        require(name.casefold() not in seen, f"Case-colliding upstream path: {name}")
        seen.add(name.casefold())
        entries.append((mode, oid, name))
    require(bool(entries), "No tracked source files found")
    for selected in selection:
        require(
            any(
                name == selected or name.startswith(selected + "/")
                for _, _, name in entries
            ),
            f"Selected path {selected} is missing at {commit}; "
            "review the source selection",
        )
    # communicate() drains both pipes while writing input, avoiding pipe-buffer
    # deadlocks for large guides. Object reads bypass export-ignore and filters.
    blobs = io.BytesIO(
        output(
            ["cat-file", "--batch"],
            cwd=cache,
            data="".join(f"{oid}\n" for _, oid, _ in entries).encode("ascii"),
        )
    )
    links: list[tuple[Path, str]] = []
    header_field_count = 3
    for mode, oid, name in entries:
        header = blobs.readline().decode("ascii").split()
        require(
            len(header) == header_field_count and header[:2] == [oid, "blob"],
            f"Missing Git blob: {name}",
        )
        size = int(header[2])
        content = blobs.read(size)
        require(
            len(content) == size and blobs.read(1) == b"\n",
            "Malformed Git blob response",
        )
        path = destination / safe_relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "120000":
            links.append((path, content.decode("utf-8")))
        else:
            path.write_bytes(content)
            path.chmod(0o755 if mode == "100755" else 0o644)
    require(blobs.read() == b"", "Unexpected trailing Git blob data")
    root = destination.resolve()
    materialized = bool(links)
    while links:
        pending: list[tuple[Path, str]] = []
        for path, target in links:
            require(
                bool(target)
                and not Path(target).is_absolute()
                and not any(char in target for char in "\\\x00:"),
                f"Unsafe tracked symlink: {path} -> {target!r}",
            )
            source = (path.parent / target).resolve()
            require(
                source.is_relative_to(root), f"Tracked symlink escapes snapshot: {path}"
            )
            if not source.is_file():
                pending.append((path, target))
                continue
            path.write_bytes(source.read_bytes())
            path.chmod(source.stat().st_mode & 0o777)
        require(
            len(pending) < len(links), "Tracked symlink target is unavailable or cyclic"
        )
        links = pending
    return materialized


def snapshot(
    root: Path, source_id: str, config: Source, destination: Path, *, locked: bool
) -> Source:
    """Fetch a branch or exact recorded commit and copy its selected tree."""
    require(bool(config.branch), "Git source branch is missing")
    current = root
    for name in (".cache", "upstreams"):
        current /= name
        ensure_directory(current)
    cache = current / f"{source_id}.git"
    if not cache.exists() and not cache.is_symlink():
        output(["init", "--bare", str(cache)])
        output(["remote", "add", "origin", config.url], cwd=cache)
    require(cache.is_dir() and not cache.is_symlink(), f"Unsafe Git cache: {cache}")
    origin = (
        output(["config", "--get", "remote.origin.url"], cwd=cache)
        .decode("utf-8")
        .strip()
    )
    require(origin == config.url, f"Unexpected origin in {cache}: {origin}")
    if locked:
        commit = config.commit or ""
        require(
            re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is not None,
            "Invalid pinned Git commit",
        )
        if run(["cat-file", "-e", f"{commit}^{{commit}}"], cwd=cache).returncode != 0:
            output(["fetch", "--depth", "1", "origin", commit], cwd=cache)
    else:
        output(["fetch", "--depth", "1", "origin", config.branch or ""], cwd=cache)
        commit = (
            output(["rev-parse", "FETCH_HEAD^{commit}"], cwd=cache)
            .decode("ascii")
            .strip()
        )
    linked = export_tree(cache, commit, config.selection, destination)
    return replace(
        config,
        commit=commit,
        transformations=(SYMLINK_TRANSFORMATION,) if linked else (),
    )
