# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Verify article extraction and pinned web source restoration."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from reference_maintenance import web
from reference_maintenance.model import MaintenanceError, Source, digest, inventory

URL = "https://developers.google.com/style/timeless-documentation"
ARTICLE = b"""<nav>Excluded navigation</nav>
<div class="devsite-article-body">
<devsite-key-takeaways-panel>Excluded summary</devsite-key-takeaways-panel>
<p>Timeless documentation is documentation <em>with durable prose</em>.</p>
<table><tr><th>Use</th><th>Avoid</th></tr>
<tr><td>A | B</td><td><code>new</code></td></tr></table>
<h2>Words and phrases to avoid</h2>
<ul><li><strong>Relative time</strong>: <a href="/style/future">plans</a>.</li></ul>
<p><a href="#words">Fragment</a>, <a href="future">relative link</a>.</p>
<script>Excluded script</script></div>
<footer>creativecommons.org/licenses/by/4.0/</footer>"""


class WebTests(unittest.TestCase):
    """Exercise HTML rendering, network boundaries, and cache integrity."""

    def test_extraction_keeps_inline_markup_tables_and_links(self) -> None:
        rendered = web.timeless_markdown(ARTICLE, URL).decode("utf-8")
        self.assertTrue(
            rendered.startswith("# Timeless documentation\n\nTimeless documentation")
        )
        self.assertIn("documentation *with durable prose*.", rendered)
        self.assertIn("| Use | Avoid |\n| --- | --- |\n| A \\| B | `new` |", rendered)
        self.assertIn("[plans](https://developers.google.com/style/future)", rendered)
        self.assertIn("[Fragment](" + URL + "#words)", rendered)
        self.assertNotIn("Excluded", rendered)

    def test_extraction_rejects_changed_markup_license_and_missing_content(
        self,
    ) -> None:
        for raw in (
            ARTICLE.replace(b"devsite-article-body", b"changed"),
            ARTICLE.replace(b"creativecommons.org/licenses/by/4.0/", b"other license"),
            ARTICLE.replace(b"Words and phrases to avoid", b"Changed heading"),
            ARTICLE + b'<div class="devsite-article-body"></div>',
        ):
            with self.subTest(raw=raw[:40]), self.assertRaises(MaintenanceError):
                web.timeless_markdown(raw, URL)

    def test_download_sets_timeout_and_bounds_and_rejects_non_https(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = URL
        response.read.return_value = ARTICLE
        with patch(
            "reference_maintenance.web.urlopen", return_value=response
        ) as opened:
            self.assertEqual(web.download(URL), ARTICLE)
            self.assertEqual(opened.call_args.kwargs["timeout"], 60)
            self.assertEqual(response.read.call_args.args, (10 * 1024 * 1024 + 1,))
            response.read.return_value = b""
            with self.assertRaises(MaintenanceError):
                web.download(URL)
            response.geturl.return_value = "http://example.invalid/"
            with self.assertRaises(MaintenanceError):
                web.download(URL)
        with self.assertRaises(MaintenanceError):
            web.download("file:///tmp/article")

    def test_locked_snapshot_restores_exact_outputs_from_html_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / ".cache/web"
            cache.mkdir(parents=True)
            (cache / f"{digest(ARTICLE)}.html").write_bytes(ARTICLE)
            destination = root / "staged"
            destination.mkdir()
            config = Source(
                kind="web",
                url=URL,
                license="CC-BY-4.0",
                files={"source.html": digest(ARTICLE)},
            )
            with patch(
                "reference_maintenance.web.download",
                side_effect=AssertionError("no network"),
            ):
                result = web.snapshot(root, "fixture", config, destination, locked=True)
            self.assertEqual(result.transformations, web.TRANSFORMATIONS)
            self.assertEqual((destination / "source.html").read_bytes(), ARTICLE)
            self.assertEqual(
                (destination / "timeless-documentation.md").read_bytes(),
                web.timeless_markdown(ARTICLE, URL),
            )

    def test_locked_snapshot_preserves_pinned_outputs_if_extraction_evolves(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "references/fixture"
            existing.mkdir(parents=True)
            (existing / "source.html").write_bytes(ARTICLE)
            (existing / "timeless-documentation.md").write_bytes(
                b"Pinned earlier extraction\n"
            )
            config = Source(
                kind="web", url=URL, license="CC-BY-4.0", files=inventory(existing)
            )
            destination = root / "staged"
            destination.mkdir()
            with patch(
                "reference_maintenance.web.timeless_markdown",
                side_effect=AssertionError("preserve outputs"),
            ):
                web.snapshot(root, "fixture", config, destination, locked=True)
            self.assertEqual(inventory(destination), config.files)
            self.assertFalse((root / ".cache").exists())

    def test_locked_snapshot_rejects_corrupt_cache_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / ".cache/web"
            cache.mkdir(parents=True)
            (cache / f"{digest(ARTICLE)}.html").write_bytes(b"corrupt")
            destination = root / "staged"
            destination.mkdir()
            config = Source(
                kind="web",
                url=URL,
                license="CC-BY-4.0",
                files={"source.html": digest(ARTICLE)},
            )
            with (
                patch(
                    "reference_maintenance.web.download",
                    side_effect=AssertionError("no network"),
                ),
                self.assertRaisesRegex(MaintenanceError, "unavailable locally"),
            ):
                web.snapshot(root, "fixture", config, destination, locked=True)
            self.assertEqual(list(destination.iterdir()), [])

    @unittest.skipIf(os.name == "nt", "POSIX directory symlink fixture")
    def test_linked_web_cache_is_rejected_without_writing_outside_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "pack"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            (root / ".cache").symlink_to(outside, target_is_directory=True)
            destination = root / "staged"
            destination.mkdir()
            config = Source(kind="web", url=URL, license="CC-BY-4.0")
            with (
                patch("reference_maintenance.web.download", return_value=ARTICLE),
                self.assertRaises(MaintenanceError),
            ):
                web.snapshot(root, "fixture", config, destination, locked=False)
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
