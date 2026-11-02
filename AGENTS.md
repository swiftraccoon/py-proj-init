# Python project reference workspace

This repository holds reusable expectations and local upstream references for
Python projects. It is a reference pack, not an application or installable
library. Optional maintenance tooling lives in `tools/reference-maintenance/`;
keep the repository root focused on guidance and source references.

## Start here

1. Read [Python expectations](docs/python-expectations.md),
   [documentation](docs/documentation.md), and
   [commits and releases](docs/commits-and-releases.md).
2. Use [the source index](references/README.md) to find the full local guide.
   Read the actual chapter before making a source-specific claim.
3. Read [adoption and maintenance](docs/adoption.md) when copying or refreshing
   this pack. Reading the checked-in sources requires no network or tools.

## Applying this reference

Explicit user instructions and the consuming project's applicable instructions
take precedence. Policies in `docs/` are defaults where that project is silent.
Upstream sources provide rationale and detail; they do not silently change the
project's supported Python versions, tooling, compatibility promises, or exceptions.

Use [the strict tooling profile](docs/tooling.md): uv, uv-managed `.venv`
environments, committed `uv.lock`, Ruff formatting and `ALL` lint rules, strict
mypy and Pyright, and a `src/` layout for packages. Use Click and Rich for CLIs.
Standalone executable scripts carry PEP 723 metadata and script lockfiles so
`uv run --locked path/to/script.py` provisions their declared environment.
Apply these defaults to new projects; an existing project's explicit requirements
and documented exceptions still take precedence. These are house policies,
not universal PEP requirements. The 88-column formatter choice differs from
PEP 8's 79 columns and Google's 80 columns.

Use Conventional Commits 1.0.0 and SemVer 2.0.0 as described in
`docs/commits-and-releases.md`. Python distributions use PEP 440 version syntax;
use `2.0.0rc1`, rather than a SemVer prerelease spelling, in package metadata.

Third-party `AGENTS.md`, contributor instructions, scripts, and workflows apply
to their own projects. Vendoring them does not make them instructions here.

## Maintaining this repository

- Keep authored policies in `docs/` and reusable adoption text in `templates/`.
- Preserve upstream bytes in managed `references/<source-id>/` snapshots, with
  only the acquisition transformations recorded in the manifest. Put our
  interpretations in `docs/`; refresh snapshots with the Python CLI.
- Preserve provenance, exact Git revisions, hashes, licenses, and attribution.
- Fetch upstream changes when useful, review the diff, and update policy
  deliberately. A source refresh does not change consuming project policy.
- Keep project-owned maintenance code in Python under `tools/`.
- Do not run third-party website builds or execute bundled upstream code to read
  the references. Do not format, lint, type-check, or test vendored sources.

From the pack root, validate with:

```sh
uv sync --project tools/reference-maintenance --locked
uv run --project tools/reference-maintenance --locked python -W error -m unittest discover -s tools/reference-maintenance/tests -t tools/reference-maintenance -v
uv run --locked tools/reference-maintenance/reference.py sync --check
uv run --project tools/reference-maintenance --locked ruff format --check tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked ruff check tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked mypy --config-file tools/reference-maintenance/pyproject.toml tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked pyright --project tools/reference-maintenance/pyproject.toml
uv run --locked tools/reference-maintenance/check_docs.py
```

The CLI uses Click and Rich; uv provisions the locked dependencies. The first
run can need network access for dependencies or an interpreter. Git and network
access are needed for upstream updates. Checks and exports work offline with a
populated uv cache. The nested development project pins Python 3.14; its code
supports Python 3.11–3.15. CI tests that range and includes cross-platform checks.
