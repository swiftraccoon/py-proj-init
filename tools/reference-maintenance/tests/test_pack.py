# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Verify checked-in reference artifacts and authored documentation."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import check_docs
from reference_maintenance import sync, web
from reference_maintenance.model import inventory, read_manifest, serialize
from reference_maintenance.sources import all_sources
from tests.support import ROOT, git


class PackTests(unittest.TestCase):
    """Check snapshot integrity, document links, and checkout portability."""

    def test_checked_in_sources_verify_and_manifest_round_trips(self) -> None:
        sync.run(ROOT, options=sync.Options(check=True), report=lambda _: None)
        sources = read_manifest(ROOT)
        self.assertEqual(set(sources), set(all_sources()))
        self.assertEqual(
            serialize(sources), (ROOT / "references/manifest.json").read_bytes()
        )

    def test_readable_web_copy_is_reproducible_from_committed_html(self) -> None:
        directory = ROOT / "references/google-timeless-documentation"
        config = all_sources()["google-timeless-documentation"]
        self.assertEqual(
            web.timeless_markdown((directory / "source.html").read_bytes(), config.url),
            (directory / "timeless-documentation.md").read_bytes(),
        )
        self.assertEqual(
            (directory / "ATTRIBUTION.md").read_text(encoding="utf-8"), web.ATTRIBUTION
        )

    def test_authored_documentation_links_resolve(self) -> None:
        self.assertEqual(check_docs.check(ROOT), [])

    @unittest.skipUnless(shutil.which("git"), "Git required for checkout fixture")
    def test_snapshot_bytes_survive_git_checkout_with_autocrlf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            source = parent / "source"
            source.mkdir()
            shutil.copyfile(ROOT / ".gitattributes", source / ".gitattributes")
            shutil.copytree(ROOT / "references", source / "references")
            git("init", cwd=source)
            git("-c", "core.autocrlf=false", "add", "--force", ".", cwd=source)
            git(
                "-c",
                "core.autocrlf=false",
                "commit",
                "-m",
                "snapshot fixture",
                cwd=source,
            )
            git(
                "clone",
                "--config",
                "core.autocrlf=true",
                str(source),
                str(parent / "checkout"),
                cwd=parent,
            )
            self.assertEqual(
                inventory(parent / "checkout/references"),
                inventory(ROOT / "references"),
            )


if __name__ == "__main__":
    unittest.main()
