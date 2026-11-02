# Python project reference

A reusable reference library for professional Python projects, modeled on
`rust-proj-init`. It includes project expectations, full
local source documents, an agent adoption template, and Python maintenance tools.
Read the guides offline or export a self-contained copy into another project.

Start with [AGENTS.md](AGENTS.md). The working policies are:

- [Python expectations](docs/python-expectations.md): environments, design,
  formatting, typing, exceptions, security, dependencies, and verification.
- [Strict tooling profile](docs/tooling.md): uv environments and scripts, Click
  and Rich CLIs, Ruff `ALL`, and strict mypy and Pyright checks.
- [Packaging and testing](docs/packaging-and-testing.md): `pyproject.toml`,
  package layout, reproducible environments, CI, and distribution checks.
- [Documentation](docs/documentation.md): docstrings and durable product writing.
- [Commits and releases](docs/commits-and-releases.md): Conventional Commits,
  SemVer compatibility policy, and PEP 440 distribution versions.
- [Adoption and maintenance](docs/adoption.md): copying, updates, and recovery.

The root is a reference library. Optional tooling is an independent project in
[`tools/reference-maintenance/`](tools/reference-maintenance/). There is no root
Python package to install and no required application framework.

## Local sources

| Source | Local entry point |
| --- | --- |
| Python PEPs | [PEP 8](references/python-peps/peps/pep-0008.rst), [PEP 257](references/python-peps/peps/pep-0257.rst), [PEP 440](references/python-peps/peps/pep-0440.rst) |
| Python Packaging User Guide | [Index](references/python-packaging/source/index.rst), [pyproject guide](references/python-packaging/source/guides/writing-pyproject-toml.rst) |
| Python typing documentation | [Type system specification](references/python-typing/docs/spec/index.rst) |
| Google Python Style Guide | [Full guide](references/google-styleguide/pyguide.md) |
| Google timeless documentation | [Readable article](references/google-timeless-documentation/timeless-documentation.md) |
| Conventional Commits 1.0.0 | [Specification](references/conventional-commits/content/v1.0.0/index.md) |
| Semantic Versioning 2.0.0 | [Specification](references/semver/spec/v2.0.0.md) |

Sources retain upstream paths, licenses, and attribution. PEPs and Google guides
use explicit selections; packaging and typing include their complete documentation
trees. Conventional Commits and SemVer include their tracked repository trees.
The timeless snapshot includes the original HTML and a readable Markdown copy.
See [provenance and licenses](references/README.md).

## Copy into a Python project

With uv installed, run from this repository:

```sh
uv run --locked tools/reference-maintenance/reference.py export /absolute/path/to/python-project
```

This creates `python-project/.python-reference/`, verifies its sources, and omits
Git metadata, virtual environments, and caches. The exporter refuses to overwrite
an existing pack and reports files excluded by the destination's Git ignore rules.
Merge the [AGENTS.md fragment](templates/AGENTS.md) into the destination's root
`AGENTS.md` so future work uses the reference. Existing project files are preserved.

The pack can instead remain in a shared checkout referenced by absolute path.
The [adoption guide](docs/adoption.md) covers both approaches and package exclusions.

## Verify or refresh

The CLI uses Click and Rich, provisioned by uv from its inline script metadata
and lockfile. Git is needed to refresh Git sources; the web source uses Python's
HTTPS client. Reading references needs no tools. Checks, tests, and exports need
no external services once uv has cached the locked dependencies and interpreter.

```sh
# Check all source hashes and recorded provenance offline.
uv run --locked tools/reference-maintenance/reference.py sync --check

# Refresh upstream snapshots, then review the diff.
uv run --locked tools/reference-maintenance/reference.py sync

# Refresh selected sources.
uv run --locked tools/reference-maintenance/reference.py sync python-peps python-packaging

# Restore the recorded revisions; matching sources stay untouched.
uv run --locked tools/reference-maintenance/reference.py sync --locked

# Run deterministic maintenance tests offline (Git fixtures require Git).
uv run --project tools/reference-maintenance --locked python -W error -m unittest discover -s tools/reference-maintenance/tests -t tools/reference-maintenance -v
```

[`references/manifest.json`](references/manifest.json) records source URLs,
selections, retrieval times, exact revisions, transformations, and SHA-256 hashes.
Git caches live in ignored `.cache/upstreams/`; web HTML is cached by content hash.
`--root /path/to/reference-pack` before a command selects another pack. By default
the CLI uses the pack containing its script, independently of the working directory.

Maintenance supports Python 3.11–3.15. Development uses uv's `.venv` with Python
3.14, Ruff `ALL`, strict mypy, and strict Pyright, including the test code. See
[maintenance development](tools/reference-maintenance/README.md) for quality checks.
The consuming project chooses its own interpreter, backend, tools, and dependencies.

[`templates/pyproject.toml`](templates/pyproject.toml) supplies the strict package
configuration. [`templates/cli_script.py`](templates/cli_script.py) is a runnable
Click/Rich script with inline dependencies and its own lockfile.

Authored guidance, templates, and tools use the [0BSD license](LICENSE), which
permits reuse without attribution or notice retention. Upstream references keep
their own licenses, including the Packaging User Guide's CC BY-SA 3.0 license;
see the [license inventory](references/README.md#licenses-and-attribution).
