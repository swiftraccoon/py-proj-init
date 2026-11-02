# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Verify, stage, and promote snapshots with edit protection and rollback."""

from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from . import git, web
from .model import (
    OS_METADATA,
    MaintenanceError,
    Source,
    atomic_write,
    ensure_directory,
    inventory,
    read_manifest,
    real_directory,
    require,
    serialize,
    timestamp,
)
from .sources import all_sources

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence


@dataclass(frozen=True)
class Options:
    """Select offline verification, pinned restoration, or edit replacement."""

    check: bool = False
    locked: bool = False
    force: bool = False


_DEFAULT_OPTIONS = Options()


@contextmanager
def operation_lock(root: Path) -> Generator[None, None, None]:
    """Exclude concurrent refresh writers with an exclusive lock file."""
    path = root / ".reference-maintenance.lock"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        message = (
            f"Maintenance lock exists: {path}; another refresh may be running. "
            "Remove a stale lock only after confirming that process has stopped."
        )
        raise MaintenanceError(message) from exc
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as stream:
            stream.write(f"pid={os.getpid()}\n")
        yield
    finally:
        path.unlink()


def _layout(references: Path, configs: dict[str, Source]) -> None:
    if not references.exists() and not references.is_symlink():
        return
    require(real_directory(references), "references/ must be a directory")
    allowed = {"README.md", "manifest.json", *configs} | OS_METADATA
    for path in references.iterdir():
        require(
            path.name in allowed,
            f"Unmanaged content in references/: {path.name}",
        )


def differences(
    directory: Path, expected: dict[str, str]
) -> tuple[list[str], list[str]]:
    """Return missing paths and edited/added paths relative to an inventory."""
    actual = (
        inventory(directory) if directory.exists() or directory.is_symlink() else {}
    )
    missing = sorted(set(expected) - actual.keys())
    changed = sorted(name for name, sha in actual.items() if expected.get(name) != sha)
    return missing, changed


class RecoveryError(MaintenanceError):
    """Rollback failed; retain staging and backups for manual recovery."""


def _rollback_files(
    references: Path, staging: Path, promoted: list[str], backups: list[str]
) -> list[str]:
    failures: list[str] = []
    moves = [
        (references / name, staging / name, f"withdraw {name}")
        for name in reversed(promoted)
    ]
    moves.extend(
        (staging / f"{name}.backup", references / name, f"restore {name}")
        for name in reversed(backups)
    )
    for source, destination, operation in moves:
        try:
            source.rename(destination)
        except (OSError, KeyboardInterrupt) as exc:
            failures.append(f"{operation}: {exc}")
    return failures


def _restore_manifest(path: Path, previous: bytes | None) -> None:
    installed = path.read_bytes() if path.exists() else None
    if installed != previous:
        if previous is None:
            path.unlink()
        else:
            atomic_write(path, previous)


def promote(
    references: Path, staging: Path, ids: Sequence[str], sources: dict[str, Source]
) -> None:
    """Install staged sources and restore snapshots and manifest on failure."""
    manifest_path = references / "manifest.json"
    previous = manifest_path.read_bytes() if manifest_path.exists() else None
    if previous is not None:
        (staging / "manifest.backup.json").write_bytes(previous)
    promoted: list[str] = []
    backups: list[str] = []
    try:
        for source_id in ids:
            destination = references / source_id
            if destination.exists() or destination.is_symlink():
                destination.rename(staging / f"{source_id}.backup")
                backups.append(source_id)
            (staging / source_id).rename(destination)
            promoted.append(source_id)
        atomic_write(manifest_path, serialize(sources))
    except (OSError, MaintenanceError, KeyboardInterrupt) as exc:
        failures = _rollback_files(references, staging, promoted, backups)
        # Cancellation can arrive just after the manifest replacement.
        try:
            _restore_manifest(manifest_path, previous)
        except (OSError, KeyboardInterrupt) as rollback:
            failures.append(f"restore manifest: {rollback}")
        if failures:
            message = (
                f"Promotion failed: {exc}; rollback errors: {'; '.join(failures)}. "
                f"Recovery files retained at {staging}"
            )
            raise RecoveryError(message) from exc
        if isinstance(exc, KeyboardInterrupt):
            raise
        message = f"Promotion failed; restored previous snapshots: {exc}"
        raise MaintenanceError(message) from exc


def _validate_record(
    source_id: str, old: Source | None, config: Source, options: Options
) -> None:
    if not (options.check or options.locked):
        return
    require(old is not None, f"{source_id}: missing manifest entry")
    if old is not None:
        drift = old.provenance_drift(config)
        require(
            not drift,
            f"{source_id}: provenance differs ({', '.join(drift)}); "
            f"run sync {source_id}",
        )


def _needs_refresh(directory: Path, old: Source | None, options: Options) -> bool:
    if options.force:
        return True
    if old is None:
        require(
            not (directory.exists() or directory.is_symlink()),
            f"{directory.name}: unmanaged snapshot; use --force to replace",
        )
        return True
    missing, changed = differences(directory, old.files)
    local_changes = changed if options.locked else changed + missing
    require(
        not local_changes,
        f"{directory.name}: local changes detected "
        f"({', '.join(local_changes[:8])}); preserve them or use --force to replace",
    )
    return not (options.locked and not (missing or changed))


def _plan(
    references: Path,
    ids: Sequence[str],
    sources: dict[str, Source],
    configs: dict[str, Source],
    options: Options,
) -> list[str]:
    work: list[str] = []
    for source_id in ids:
        directory = references / source_id
        old = sources.get(source_id)
        _validate_record(source_id, old, configs[source_id], options)
        if options.check:
            if old is None:
                message = f"{source_id}: missing manifest entry"
                raise MaintenanceError(message)
            missing, changed = differences(directory, old.files)
            require(
                not (missing or changed),
                f"{source_id}: snapshot differs: {', '.join((changed + missing)[:8])}",
            )
        elif _needs_refresh(directory, old, options):
            work.append(source_id)
    return work


def run(
    root: Path,
    source_ids: Sequence[str] = (),
    options: Options = _DEFAULT_OPTIONS,
    *,
    configs: dict[str, Source] | None = None,
    report: Callable[[str], None] = print,
) -> None:
    """Check offline, refresh selected sources, or restore exact revisions."""
    require(not (options.check and options.locked), "Choose --check or --locked")
    require(not (options.check and options.force), "--force has no effect with --check")
    root = root.resolve(strict=True)
    configs = configs if configs is not None else all_sources()
    ids = list(dict.fromkeys(source_ids or sorted(configs)))
    require(bool(ids), "No source definitions")
    for source_id in ids:
        require(
            source_id in configs,
            f"Unknown source {source_id}; choose: {', '.join(sorted(configs))}",
        )
    if options.check:
        _run(root, ids, configs, options, report)
    else:
        with operation_lock(root):
            _run(root, ids, configs, options, report)


def _run(
    root: Path,
    ids: list[str],
    configs: dict[str, Source],
    options: Options,
    report: Callable[[str], None],
) -> None:
    references = root / "references"
    _layout(references, configs)
    sources = read_manifest(root)
    require(
        not (sources.keys() - configs.keys()), "Manifest has unsupported source IDs"
    )
    work = _plan(references, ids, sources, configs, options)
    for source_id in ids:
        if source_id not in work:
            label = "OK" if options.check else "Unchanged"
            report(f"{label} {source_id}: {len(sources[source_id].files)} files")
    if not work:
        return
    ensure_directory(references)
    staging = Path(tempfile.mkdtemp(prefix=".reference-sync-", dir=references))
    retain = False
    try:
        pending = dict(sources)
        for source_id in work:
            destination = staging / source_id
            destination.mkdir()
            old = sources.get(source_id)
            config = old if options.locked and old is not None else configs[source_id]
            fetch = git.snapshot if config.kind == "git" else web.snapshot
            source = fetch(root, source_id, config, destination, locked=options.locked)
            files = inventory(destination)
            require(bool(files), f"{source_id}: upstream produced an empty snapshot")
            source = replace(
                source,
                files=files,
                retrieved_at=config.retrieved_at if options.locked else timestamp(),
            )
            if options.locked:
                require(
                    source == old,
                    f"{source_id}: pinned snapshot does not match manifest",
                )
            pending[source_id] = source
        promote(references, staging, work, pending)
        for source_id in work:
            report(f"Updated {source_id}: {len(pending[source_id].files)} files")
    except RecoveryError:
        retain = True
        raise
    finally:
        if not retain:
            shutil.rmtree(staging)
