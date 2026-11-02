# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Verify manifest validation and portable file operations."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reference_maintenance.model import (
    MaintenanceError,
    Source,
    atomic_write,
    digest,
    inventory,
    read_manifest,
    safe_relative,
    serialize,
)


class ModelTests(unittest.TestCase):
    """Exercise inventories, schema validation, and atomic writes."""

    def test_hash_and_inventory_include_hidden_files_and_detect_edits(self) -> None:
        self.assertEqual(
            digest(b"hello world"),
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".hidden").write_bytes(b"first")
            (root / ".DS_Store").write_bytes(b"Finder")
            original = inventory(root)
            self.assertEqual(set(original), {".hidden"})
            (root / ".hidden").write_bytes(b"second")
            self.assertNotEqual(inventory(root), original)

    def test_safe_paths_reject_escape_and_platform_ambiguity(self) -> None:
        for name in (
            "",
            ".",
            "..",
            "../outside",
            "/absolute/guide",
            "C:/guide",
            "a\\b",
            "a//b",
            "a/./b",
            ".git/config",
            "a\x00b",
        ):
            with self.subTest(name=name), self.assertRaises(MaintenanceError):
                safe_relative(name)
        self.assertEqual(str(safe_relative("docs/guide.md")), "docs/guide.md")

    def test_inventory_rejects_symlinks(self) -> None:
        if os.name == "nt":
            self.skipTest("Windows symlinks require developer mode or elevation")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "link").symlink_to("missing")
            with self.assertRaisesRegex(MaintenanceError, "symlink"):
                inventory(root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO is a POSIX fixture")
    def test_inventory_rejects_fifo_without_opening_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.mkfifo(root / "pipe")
            with self.assertRaisesRegex(MaintenanceError, "nonregular"):
                inventory(root)

    def test_manifest_round_trip_and_rejection_of_invalid_data(self) -> None:
        source = Source(
            kind="git",
            url="https://example.invalid/source.git",
            branch="main",
            license="MIT",
            commit="a" * 40,
            retrieved_at="2026-11-01T00:00:00Z",
            files={"guide.md": digest(b"guide")},
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "references").mkdir()
            path = root / "references/manifest.json"
            path.write_bytes(serialize({"fixture": source}))
            self.assertEqual(read_manifest(root), {"fixture": source})
            self.assertEqual(serialize(read_manifest(root)), path.read_bytes())
            original = json.loads(path.read_bytes())
            for field, value in (
                ("commit", "main"),
                ("files", {"../outside": "a" * 64}),
                ("files", {"guide": "bad"}),
                ("retrieved_at", "yesterday"),
            ):
                document = json.loads(json.dumps(original))
                document["sources"]["fixture"][field] = value
                path.write_text(json.dumps(document), encoding="utf-8")
                with (
                    self.subTest(field=field, value=value),
                    self.assertRaises(MaintenanceError),
                ):
                    read_manifest(root)
            original["schema_version"] = 2
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(MaintenanceError, "version"):
                read_manifest(root)

    def test_failed_atomic_write_preserves_file_and_removes_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "manifest.json"
            path.write_bytes(b"original")
            with (
                patch.object(Path, "replace", side_effect=OSError("cannot replace")),
                self.assertRaises(OSError),
            ):
                atomic_write(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"original")
            self.assertEqual(list(root.iterdir()), [path])

    def test_successful_atomic_write_has_portable_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            atomic_write(path, b"{}\n")
            self.assertEqual(path.read_bytes(), b"{}\n")
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
