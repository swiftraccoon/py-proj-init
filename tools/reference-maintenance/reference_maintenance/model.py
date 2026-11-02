# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Source records, portable file inventories, and atomic manifest writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import cast

OS_METADATA = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})
PROVENANCE = ("kind", "url", "branch", "selection", "license")


class MaintenanceError(Exception):
    """A reference operation failed with a diagnostic suitable for the CLI."""


def require(condition: bool, message: str) -> None:  # noqa: FBT001 -- validation predicate
    """Raise a user-facing error when a required invariant is absent."""
    if not condition:
        raise MaintenanceError(message)


def safe_relative(name: str) -> PurePosixPath:
    """Validate a relative, portable snapshot path before joining it to a root."""
    path = PurePosixPath(name)
    require(
        bool(name)
        and bool(path.parts)
        and not path.is_absolute()
        and path.as_posix() == name
        and all(part not in {".", "..", ".git"} for part in path.parts)
        and not any(char in name for char in "\\\x00\r\n:"),
        f"Unsafe snapshot path: {name!r}",
    )
    return path


def real_directory(path: Path) -> bool:
    """Return whether the path itself is a directory rather than a link."""
    try:
        return stat.S_ISDIR(path.lstat().st_mode)
    except FileNotFoundError:
        return False


def ensure_directory(path: Path) -> None:
    """Create a directory and reject links or files at that path."""
    path.mkdir(exist_ok=True)
    require(real_directory(path), f"Expected a directory, not a symlink: {path}")


def digest(data: bytes) -> str:
    """Return the SHA-256 digest used by snapshot inventories."""
    return hashlib.sha256(data).hexdigest()


def inventory(directory: Path) -> dict[str, str]:
    """Hash every regular file, including hidden files; reject links and devices."""
    require(real_directory(directory), f"Expected snapshot directory: {directory}")
    files: dict[str, str] = {}

    def visit(current: Path) -> None:
        for path in sorted(current.iterdir()):
            mode = path.lstat().st_mode
            require(not stat.S_ISLNK(mode), f"Snapshot contains a symlink: {path}")
            if path.name in OS_METADATA:
                continue
            name = path.relative_to(directory).as_posix()
            safe_relative(name)
            if stat.S_ISDIR(mode):
                visit(path)
            else:
                require(
                    stat.S_ISREG(mode), f"Snapshot contains a nonregular file: {path}"
                )
                files[name] = digest(path.read_bytes())

    visit(directory)
    return dict(sorted(files.items()))


def atomic_write(path: Path, data: bytes) -> None:
    """Replace one file atomically, removing the temporary file on failure."""
    descriptor, temporary_name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def timestamp() -> str:
    """Return the retrieval time as RFC 3339 UTC, to whole seconds."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _object(value: object, context: str) -> dict[str, object]:
    require(isinstance(value, dict), f"{context} must be an object")
    result = cast("dict[object, object]", value)
    require(all(isinstance(key, str) for key in result), f"Invalid keys in {context}")
    return cast("dict[str, object]", result)


def _string(value: object, context: str) -> str:
    require(isinstance(value, str), f"{context} must be a string")
    return cast("str", value)


def _strings(value: object, context: str) -> tuple[str, ...]:
    require(isinstance(value, list), f"{context} must be a list")
    return tuple(_string(item, context) for item in cast("list[object]", value))


@dataclass
class Source:
    """Acquisition configuration plus the provenance of a materialized source."""

    kind: str
    url: str
    license: str
    branch: str | None = None
    selection: tuple[str, ...] = ()
    transformations: tuple[str, ...] = ()
    commit: str | None = None
    retrieved_at: str = ""
    files: dict[str, str] = field(default_factory=dict[str, str])

    def provenance_drift(self, other: Source) -> list[str]:
        """List acquisition fields that no longer match the tool's source config."""
        return [
            name for name in PROVENANCE if getattr(self, name) != getattr(other, name)
        ]

    @classmethod
    def from_json(cls, value: object) -> Source:
        """Validate manifest data before it can affect filesystem operations."""
        record = _object(value, "source")
        require(set(record) == set(cls.__dataclass_fields__), "Invalid source fields")
        kind = _string(record["kind"], "kind")
        require(kind in {"git", "web"}, f"Unsupported source kind: {kind}")
        branch = record["branch"]
        require(branch is None or isinstance(branch, str), "Invalid branch")
        selection = _strings(record["selection"], "selection")
        for selected in selection:
            safe_relative(selected)
        commit = record["commit"]
        require(commit is None or isinstance(commit, str), "Invalid commit")
        if kind == "git":
            require(
                isinstance(commit, str)
                and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is not None,
                "Invalid pinned Git commit",
            )
            require(bool(branch), "Git source needs a branch")
        else:
            require(commit is None and branch is None, "Web source has Git metadata")
        retrieved = _string(record["retrieved_at"], "retrieved_at")
        try:
            parsed = datetime.strptime(retrieved, "%Y-%m-%dT%H:%M:%S%z")
            require(
                parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == retrieved,
                "Retrieval timestamp must be canonical UTC",
            )
        except ValueError as exc:
            msg = f"Invalid UTC retrieval timestamp: {retrieved}"
            raise MaintenanceError(msg) from exc
        files: dict[str, str] = {}
        for name, hash_value in _object(record["files"], "files").items():
            safe_relative(name)
            sha = _string(hash_value, f"hash for {name}")
            require(
                re.fullmatch(r"[0-9a-f]{64}", sha) is not None, f"Invalid hash: {name}"
            )
            files[name] = sha
        require(bool(files), "Snapshot inventory is empty")
        return cls(
            kind=kind,
            url=_string(record["url"], "url"),
            license=_string(record["license"], "license"),
            branch=cast("str | None", branch),
            selection=selection,
            transformations=_strings(record["transformations"], "transformations"),
            commit=cast("str | None", commit),
            retrieved_at=retrieved,
            files=files,
        )


def read_manifest(root: Path) -> dict[str, Source]:
    """Read a versioned manifest, treating an absent file as an unpopulated pack."""
    path = root / "references/manifest.json"
    if not path.exists() and not path.is_symlink():
        return {}
    require(not path.is_symlink(), f"Manifest must be a regular file: {path}")
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        msg = f"Cannot parse {path}: {exc}"
        raise MaintenanceError(msg) from exc
    record = _object(raw, "manifest")
    require(set(record) == {"schema_version", "sources"}, "Invalid manifest fields")
    require(type(record["schema_version"]) is int, "Invalid manifest version")
    require(record["schema_version"] == 1, "Unsupported manifest version")
    sources: dict[str, Source] = {}
    for name, value in _object(record["sources"], "sources").items():
        require(
            re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None,
            "Invalid source ID",
        )
        sources[name] = Source.from_json(value)
    return sources


def serialize(sources: dict[str, Source]) -> bytes:
    """Produce deterministic JSON, including a final newline."""
    return (
        json.dumps(
            {
                "schema_version": 1,
                "sources": {k: asdict(v) for k, v in sources.items()},
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
