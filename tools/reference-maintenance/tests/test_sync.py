# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Exercise local Git synchronization and transactional recovery."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from reference_maintenance import sync
from reference_maintenance.git import export_tree, snapshot
from reference_maintenance.model import (
    MaintenanceError,
    Source,
    atomic_write,
    inventory,
    read_manifest,
    serialize,
)
from tests.support import git, upstream


@unittest.skipUnless(shutil.which("git"), "Git required for local integration fixtures")
class SyncTests(unittest.TestCase):
    """Check refresh, restoration, local edits, and rollback."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)
        self.root = self.parent / "pack"
        self.root.mkdir()
        self.upstream, self.config = upstream(self.parent)
        self.configs = {"fixture": self.config}

    def refresh(self, **kwargs: bool) -> None:
        sync.run(
            self.root,
            options=sync.Options(**kwargs),
            configs=self.configs,
            report=lambda _: None,
        )

    def test_refresh_check_and_locked_restore_preserve_exact_bytes(self) -> None:
        self.refresh()
        manifest = (self.root / "references/manifest.json").read_bytes()
        self.assertEqual(
            (self.root / "references/fixture/guide.md").read_bytes(),
            b"Original guide\r\n",
        )
        self.assertTrue((self.root / "references/fixture/.gitattributes").is_file())
        with patch(
            "reference_maintenance.git.run",
            side_effect=AssertionError("check must be offline"),
        ):
            self.refresh(check=True)
            self.refresh(locked=True)
        (self.root / "references/fixture/guide.md").unlink()
        self.refresh(locked=True)
        self.assertEqual(
            (self.root / "references/manifest.json").read_bytes(), manifest
        )
        self.refresh(check=True)

    def test_local_edits_and_additions_require_force(self) -> None:
        self.refresh()
        path = self.root / "references/fixture/guide.md"
        path.write_bytes(b"local edits")
        for options in ({}, {"check": True}, {"locked": True}):
            with self.subTest(options=options), self.assertRaises(MaintenanceError):
                self.refresh(**options)
        self.assertEqual(path.read_bytes(), b"local edits")
        self.refresh(locked=True, force=True)
        added = path.parent / "extra.md"
        added.write_bytes(b"local addition")
        with self.assertRaisesRegex(MaintenanceError, "local changes"):
            self.refresh(locked=True)
        self.refresh(force=True)
        self.assertFalse(added.exists())

    def test_normal_refresh_protects_missing_files_while_locked_restores_them(
        self,
    ) -> None:
        self.refresh()
        (self.root / "references/fixture/LICENSE").unlink()
        with self.assertRaisesRegex(MaintenanceError, "local changes"):
            self.refresh()
        self.refresh(locked=True)
        self.refresh(check=True)

    def test_locked_restore_uses_recorded_commit_after_branch_advances_and_is_deleted(
        self,
    ) -> None:
        self.refresh()
        original = (self.root / "references/manifest.json").read_bytes()
        (self.upstream / "guide.md").write_bytes(b"upstream update")
        git("add", "--all", cwd=self.upstream)
        git("commit", "-m", "update", cwd=self.upstream)
        git("branch", "-m", "renamed", cwd=self.upstream)
        # Force a fresh fetch; TemporaryDirectory handles cleanup of Git's
        # read-only object files on Windows.
        (self.root / ".cache").rename(self.parent / "retired-cache")
        (self.root / "references/fixture/guide.md").unlink()
        self.refresh(locked=True)
        self.assertEqual(
            (self.root / "references/manifest.json").read_bytes(), original
        )
        self.assertEqual(
            (self.root / "references/fixture/guide.md").read_bytes(),
            b"Original guide\r\n",
        )

    def test_missing_selected_path_does_not_promote_other_sources(self) -> None:
        self.refresh()
        before = inventory(self.root / "references")
        changed = replace(self.config, selection=("guide.md", "missing-license"))
        with self.assertRaisesRegex(MaintenanceError, "Selected path"):
            sync.run(self.root, configs={"fixture": changed}, report=lambda _: None)
        self.assertEqual(inventory(self.root / "references"), before)
        self.assertFalse((self.root / ".reference-maintenance.lock").exists())

    def test_fetch_failure_leaves_snapshots_and_manifest_unchanged(self) -> None:
        self.refresh()
        before = inventory(self.root / "references")
        with (
            patch(
                "reference_maintenance.git.snapshot",
                side_effect=MaintenanceError("fetch failed"),
            ),
            self.assertRaisesRegex(MaintenanceError, "fetch failed"),
        ):
            self.refresh()
        self.assertEqual(inventory(self.root / "references"), before)
        self.assertFalse(list((self.root / "references").glob(".reference-sync-*")))

    def test_manifest_install_failure_rolls_back_promoted_snapshots(self) -> None:
        self.refresh()
        before = inventory(self.root / "references")
        (self.upstream / "guide.md").write_bytes(b"new upstream bytes")
        git("add", "--all", cwd=self.upstream)
        git("commit", "-m", "update", cwd=self.upstream)
        with (
            patch(
                "reference_maintenance.sync.atomic_write",
                side_effect=OSError("disk full"),
            ),
            self.assertRaisesRegex(MaintenanceError, "restored previous snapshots"),
        ):
            self.refresh()
        self.assertEqual(inventory(self.root / "references"), before)

    def test_cancellation_after_manifest_commit_restores_files_and_manifest(
        self,
    ) -> None:
        self.refresh()
        before = inventory(self.root / "references")
        (self.upstream / "guide.md").write_bytes(b"new upstream bytes")
        git("add", "--all", cwd=self.upstream)
        git("commit", "-m", "update", cwd=self.upstream)
        writer = atomic_write
        calls = 0

        def interrupt_after_write(path: Path, data: bytes) -> None:
            nonlocal calls
            writer(path, data)
            calls += 1
            if calls == 1:
                raise KeyboardInterrupt

        with (
            patch(
                "reference_maintenance.sync.atomic_write",
                side_effect=interrupt_after_write,
            ),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.refresh()
        self.assertEqual(inventory(self.root / "references"), before)
        self.assertFalse((self.root / ".reference-maintenance.lock").exists())

    def test_failed_rollback_retains_previous_snapshots_and_manifest_for_recovery(
        self,
    ) -> None:
        self.refresh()
        previous = (self.root / "references/manifest.json").read_bytes()
        rename = Path.rename

        def reject_rollback(path: Path, target: Path) -> Path:
            if path.name == "fixture.backup":
                msg = "rollback blocked"
                raise OSError(msg)
            return rename(path, target)

        with (
            patch.object(Path, "rename", reject_rollback),
            patch(
                "reference_maintenance.sync.atomic_write",
                side_effect=OSError("install blocked"),
            ),
            self.assertRaisesRegex(sync.RecoveryError, "Recovery files retained"),
        ):
            self.refresh()
        staging = list((self.root / "references").glob(".reference-sync-*"))
        self.assertEqual(len(staging), 1)
        self.assertEqual(
            (staging[0] / "fixture.backup/guide.md").read_bytes(), b"Original guide\r\n"
        )
        self.assertEqual((staging[0] / "manifest.backup.json").read_bytes(), previous)

    def test_all_sources_are_staged_before_promotion_and_partial_installs_roll_back(
        self,
    ) -> None:
        self.configs["second"] = self.config
        self.refresh()
        before = inventory(self.root / "references")
        fetch = snapshot

        def fail_second(
            root: Path,
            source_id: str,
            config: Source,
            destination: Path,
            *,
            locked: bool,
        ) -> Source:
            if source_id == "second":
                msg = "second fetch failed"
                raise MaintenanceError(msg)
            return fetch(root, source_id, config, destination, locked=locked)

        with (
            patch("reference_maintenance.git.snapshot", side_effect=fail_second),
            self.assertRaisesRegex(MaintenanceError, "second fetch failed"),
        ):
            self.refresh()
        self.assertEqual(inventory(self.root / "references"), before)
        rename = Path.rename

        def fail_second_install(path: Path, target: Path) -> Path:
            if path.name == "second" and path.parent.name.startswith(
                ".reference-sync-"
            ):
                msg = "second install failed"
                raise OSError(msg)
            return rename(path, target)

        with (
            patch.object(Path, "rename", fail_second_install),
            self.assertRaisesRegex(MaintenanceError, "restored previous snapshots"),
        ):
            self.refresh()
        self.assertEqual(inventory(self.root / "references"), before)

    def test_bad_modes_unknown_sources_and_provenance_fail_before_fetch(self) -> None:
        self.refresh()
        for kwargs in ({"check": True, "locked": True}, {"check": True, "force": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(MaintenanceError):
                self.refresh(**kwargs)
        with self.assertRaisesRegex(MaintenanceError, "Unknown source"):
            sync.run(self.root, ["unknown"], configs=self.configs)
        sources = read_manifest(self.root)
        sources["fixture"].url = "https://example.invalid/other.git"
        (self.root / "references/manifest.json").write_bytes(serialize(sources))
        for kwargs in ({"check": True}, {"locked": True}):
            with self.assertRaisesRegex(MaintenanceError, "provenance differs"):
                self.refresh(**kwargs)

    def test_writer_lock_and_interrupted_staging_are_not_silently_ignored(self) -> None:
        (self.root / ".reference-maintenance.lock").write_text(
            "another process", encoding="utf-8"
        )
        with self.assertRaisesRegex(MaintenanceError, "lock exists"):
            self.refresh()
        (self.root / ".reference-maintenance.lock").unlink()
        (self.root / "references/.reference-sync-interrupted").mkdir(parents=True)
        with self.assertRaisesRegex(MaintenanceError, "Unmanaged content"):
            self.refresh()

    @unittest.skipIf(os.name == "nt", "POSIX symlink fixture")
    def test_symlinks_materialized_but_escaping_and_cyclic_links_rejected(self) -> None:
        (self.upstream / "link.md").symlink_to("guide.md")
        git("add", "--all", cwd=self.upstream)
        git("commit", "-m", "link", cwd=self.upstream)
        self.refresh()
        copied = self.root / "references/fixture/link.md"
        self.assertFalse(copied.is_symlink())
        self.assertEqual(copied.read_bytes(), b"Original guide\r\n")
        for target in ("../outside", "link.md"):
            (self.upstream / "link.md").unlink()
            (self.upstream / "link.md").symlink_to(target)
            git("add", "--all", cwd=self.upstream)
            git("commit", "-m", "invalid link", cwd=self.upstream)
            with self.assertRaises(MaintenanceError):
                self.refresh()
            self.assertEqual(copied.read_bytes(), b"Original guide\r\n")

    @unittest.skipIf(os.name == "nt", "POSIX directory symlink fixture")
    def test_reference_and_cache_directory_links_are_rejected(self) -> None:
        outside = self.parent / "outside"
        outside.mkdir()
        (self.root / "references").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(MaintenanceError):
            self.refresh(force=True)
        (self.root / "references").unlink()
        (self.root / ".cache").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(MaintenanceError):
            self.refresh(force=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_case_collisions_and_submodules_are_rejected(self) -> None:
        destination = self.parent / "staged"
        destination.mkdir()
        with (
            patch(
                "reference_maintenance.git.output",
                return_value=(
                    b"100644 blob "
                    + b"a" * 40
                    + b"\tGuide.md\0"
                    + b"100644 blob "
                    + b"b" * 40
                    + b"\tguide.md\0"
                ),
            ),
            self.assertRaisesRegex(MaintenanceError, "Case-colliding"),
        ):
            export_tree(self.upstream, "a" * 40, (), destination)
        with (
            patch(
                "reference_maintenance.git.output",
                return_value=b"160000 commit " + b"a" * 40 + b"\tmodule\0",
            ),
            self.assertRaisesRegex(MaintenanceError, "Unsupported Git entry"),
        ):
            export_tree(self.upstream, "a" * 40, (), destination)


if __name__ == "__main__":
    unittest.main()
