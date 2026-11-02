# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Explicit upstream selections; policy interpretations belong in docs/."""

from .model import Source


def all_sources() -> dict[str, Source]:
    """Return independent source definitions without retrieval metadata."""
    sources = {
        "python-peps": Source(
            kind="git",
            url="https://github.com/python/peps.git",
            branch="main",
            license=(
                "Selected PEPs: public domain or CC0-1.0; see each Copyright section"
            ),
            selection=(
                "README.rst",
                *(
                    f"peps/pep-{number:04}.rst"
                    for number in (
                        8,
                        20,
                        257,
                        440,
                        484,
                        517,
                        518,
                        561,
                        621,
                        639,
                        660,
                        723,
                        735,
                    )
                ),
            ),
        ),
        "python-packaging": Source(
            kind="git",
            url="https://github.com/pypa/packaging.python.org.git",
            branch="main",
            license=(
                "CC-BY-SA-3.0; see README.rst; retain attribution and share-alike terms"
            ),
            selection=("README.rst", "authors.txt", "source"),
        ),
        "python-typing": Source(
            kind="git",
            url="https://github.com/python/typing.git",
            branch="main",
            license="PSF-2.0 and historical notices; see LICENSE",
            selection=("README.md", "LICENSE", "docs"),
        ),
        "google-styleguide": Source(
            kind="git",
            url="https://github.com/google/styleguide.git",
            branch="gh-pages",
            license="Guides: CC-BY-3.0; code samples: Apache-2.0; see README.md",
            selection=("README.md", "LICENSE", "pyguide.md", "pylintrc", "docguide"),
        ),
        "google-timeless-documentation": Source(
            kind="web",
            url="https://developers.google.com/style/timeless-documentation",
            license="Text: CC-BY-4.0; code samples: Apache-2.0",
        ),
        "conventional-commits": Source(
            kind="git",
            url="https://github.com/conventional-commits/conventionalcommits.org.git",
            branch="master",
            license="Repository: MIT; published specification: CC-BY-3.0 (site footer)",
        ),
        "semver": Source(
            kind="git",
            url="https://github.com/semver/semver.org.git",
            branch="gh-pages",
            license="CC-BY-3.0; see specification attribution",
        ),
    }
    return dict(sorted(sources.items()))
