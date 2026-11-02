# Local upstream references

Read these documents directly; website builds and submodule initialization are
unnecessary. [`manifest.json`](manifest.json) records URLs, selected paths,
retrieval times, exact Git commits, transformations, and each file's SHA-256 hash.

| Source ID | Local entry point | Upstream |
| --- | --- | --- |
| `python-peps` | [PEP 8](python-peps/peps/pep-0008.rst), [PEP 20](python-peps/peps/pep-0020.rst), [PEP 257](python-peps/peps/pep-0257.rst), [PEP 440](python-peps/peps/pep-0440.rst) | [python/peps](https://github.com/python/peps) |
| `python-packaging` | [Guide index](python-packaging/source/index.rst), [pyproject guide](python-packaging/source/guides/writing-pyproject-toml.rst), [src layout](python-packaging/source/discussions/src-layout-vs-flat-layout.rst) | [PyPA guide](https://packaging.python.org/), [source](https://github.com/pypa/packaging.python.org) |
| `python-typing` | [Specification](python-typing/docs/spec/index.rst), [documentation index](python-typing/docs/index.rst) | [typing.python.org](https://typing.python.org/), [source](https://github.com/python/typing) |
| `google-styleguide` | [Python guide](google-styleguide/pyguide.md), [documentation guides](google-styleguide/docguide/README.md) | [google/styleguide](https://github.com/google/styleguide), [rendered Python guide](https://google.github.io/styleguide/pyguide.html) |
| `google-timeless-documentation` | [Readable article](google-timeless-documentation/timeless-documentation.md), [original HTML](google-timeless-documentation/source.html) | [Timeless documentation](https://developers.google.com/style/timeless-documentation) |
| `conventional-commits` | [1.0.0 specification](conventional-commits/content/v1.0.0/index.md), [README](conventional-commits/README.md) | [Source repository](https://github.com/conventional-commits/conventionalcommits.org) |
| `semver` | [2.0.0 specification](semver/spec/v2.0.0.md), [README](semver/README.md) | [semver.org](https://semver.org/), [source](https://github.com/semver/semver.org) |

## Selections and applicability

Each selected document is complete, rather than a summary. The PEP selection
includes style (8, 20, 257), versions (440), typing (484, 561), build isolation
and metadata (517, 518, 621), licensing (639), editable builds (660), and dependency
groups (735), and inline script metadata (723), with each document's copyright
section. PEPs can refer to historical
or superseded behavior; use the maintained PyPA and typing specifications for
their evolving standards.

The packaging `source/` and typing `docs/` trees are preserved with supporting
files and upstream notices. Google is limited to its Python and documentation
guides, README, license, and Pylint example. The presence of `pylintrc` is reference
material, not a requirement to use Pylint in a Ruff-based project. Conventional
Commits and SemVer retain tracked trees, including translations and site assets.
Tracked symlinks are copied from their in-snapshot targets; this is recorded in
the manifest. The timeless article includes original HTML, attribution, and a
mechanically generated Markdown reading copy with navigation omitted.

## Licenses and attribution

Upstream materials retain their licenses. The repository's 0BSD license does not
relicense them. Keep each source directory, notices, and manifest together when
redistributing the references; respect the relevant attribution and share-alike
conditions when adapting source text.

- Selected PEPs: public domain or CC0-1.0 as declared by each PEP's `Copyright`
  section. In particular, retain the full documents and their author information.
- Python Packaging User Guide: CC BY-SA 3.0, declared in its
  [README](python-packaging/README.rst#license). The snapshot includes its
  [author list](python-packaging/authors.txt). Share-alike terms apply to adapted
  guide material; authored policy in `docs/` is kept separate.
- Python typing documentation: [PSF license and historical notices](python-typing/LICENSE).
- Google guides: [CC BY 3.0](google-styleguide/LICENSE); code samples are Apache-2.0
  as stated in the [README](google-styleguide/README.md#licensing). Preserve any
  file-specific notices in the selected tree.
- Google timeless documentation: CC BY 4.0 text and Apache-2.0 code samples,
  except where otherwise noted; see [attribution](google-timeless-documentation/ATTRIBUTION.md)
  and the original HTML notice.
- Conventional Commits: [MIT repository license](conventional-commits/LICENSE);
  the published specification's CC BY 3.0 notice appears in
  [site configuration](conventional-commits/config.yaml).
- Semantic Versioning: CC BY 3.0, stated in the
  [specification](semver/spec/v2.0.0.md).

## Maintenance

Do not edit managed snapshots by hand. Put house interpretations in `../docs/`.
From the pack root:

```sh
uv run --locked tools/reference-maintenance/reference.py sync --check
uv run --locked tools/reference-maintenance/reference.py sync
```

Review snapshot and manifest changes. See [adoption and maintenance](../docs/adoption.md)
for selected-source refreshes, exact restores, exports, and failure recovery.
