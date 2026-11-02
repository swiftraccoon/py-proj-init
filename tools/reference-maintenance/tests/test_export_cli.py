# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Verify self-contained exports and public command behavior."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reference_maintenance import export
from reference_maintenance.model import MaintenanceError, inventory
from tests.support import ROOT, git


class ExportTests(unittest.TestCase):
    """Check pack copies, project preservation, and export failures."""

    def test_export_is_self_contained_and_preserves_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            instructions = project / "AGENTS.md"
            instructions.write_bytes(b"Existing project rules\n")
            (project / "pyproject.toml").write_bytes(b"# Existing project config\n")
            result = export.run(ROOT, project)
            self.assertEqual(instructions.read_bytes(), b"Existing project rules\n")
            self.assertEqual(
                (project / "pyproject.toml").read_bytes(),
                b"# Existing project config\n",
            )
            self.assertEqual(
                inventory(result.destination / "references"),
                inventory(ROOT / "references"),
            )
            for path in result.destination.rglob("*"):
                self.assertNotIn(path.name, export.EXCLUDED)
            tool = result.destination / "tools/reference-maintenance/reference.py"
            process = subprocess.run(  # noqa: S603 -- trusted interpreter; no shell
                [sys.executable, "-B", str(tool), "sync", "--check"],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stdout.count("OK "), 7)
            docs = subprocess.run(  # noqa: S603 -- trusted interpreter; no shell
                [sys.executable, "-B", str(tool.with_name("check_docs.py"))],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(docs.returncode, 0, docs.stderr)
            # A copied pack can export another pack without the original checkout.
            second = project / "second-project"
            second.mkdir()
            copied = subprocess.run(  # noqa: S603 -- trusted interpreter; no shell
                [sys.executable, "-B", str(tool), "export", str(second)],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(copied.returncode, 0, copied.stderr)
            self.assertTrue((second / ".python-reference/LICENSE").is_file())
            with self.assertRaisesRegex(MaintenanceError, "already exists"):
                export.run(ROOT, project)

    def test_export_rejects_missing_project_and_in_tree_destination(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaises(FileNotFoundError),
        ):
            export.run(ROOT, Path(temporary) / "missing")
        with self.assertRaisesRegex(MaintenanceError, "outside"):
            export.run(ROOT, ROOT / "docs")

    @unittest.skipIf(os.name == "nt", "POSIX dangling symlink fixture")
    def test_export_refuses_dangling_destination_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".python-reference").symlink_to("missing")
            with self.assertRaisesRegex(MaintenanceError, "already exists"):
                export.run(ROOT, project)
            self.assertTrue((project / ".python-reference").is_symlink())

    @unittest.skipUnless(shutil.which("git"), "Git required for ignore-rule fixture")
    def test_export_reports_files_ignored_by_consuming_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            git("init", cwd=project)
            (project / ".gitignore").write_text("*.rst\n", encoding="utf-8")
            result = export.run(ROOT, project)
            self.assertTrue(
                any(name.endswith("pep-0008.rst") for name in result.ignored_by_git)
            )
            self.assertTrue(result.destination.is_dir())

    def test_corrupt_source_is_not_exported_and_staging_is_cleaned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            source_project = parent / "source"
            source_project.mkdir()
            source = export.run(ROOT, source_project).destination
            (source / "references/python-peps/peps/pep-0008.rst").write_bytes(
                b"corrupt"
            )
            project = parent / "target"
            project.mkdir()
            with self.assertRaisesRegex(MaintenanceError, "snapshot differs"):
                export.run(source, project)
            self.assertEqual(list(project.iterdir()), [])


class CliTests(unittest.TestCase):
    """Exercise argument validation and reference-root discovery."""

    def invoke(
        self, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 -- trusted interpreter; no shell
            [
                sys.executable,
                "-B",
                str(ROOT / "tools/reference-maintenance/reference.py"),
                *args,
            ],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_default_root_is_independent_of_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.invoke("sync", "--check", cwd=Path(temporary))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("OK "), 7)

    def test_help_and_invalid_arguments_have_useful_exit_statuses(self) -> None:
        self.assertEqual(self.invoke("--help").returncode, 0)
        self.assertEqual(self.invoke().returncode, 0)
        for args in (("sync", "--check", "--locked"), ("export",), ("unknown",)):
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        result = self.invoke("sync", "--check", "unknown-source")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown source", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
