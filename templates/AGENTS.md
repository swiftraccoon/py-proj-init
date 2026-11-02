## Python project references

Read `.python-reference/docs/python-expectations.md`,
`.python-reference/docs/tooling.md`,
`.python-reference/docs/packaging-and-testing.md`,
`.python-reference/docs/documentation.md`, and
`.python-reference/docs/commits-and-releases.md` before substantive work.
Use `.python-reference/references/README.md` to find full local upstream guides.
Read the relevant source chapter before making source-specific claims.

These are defaults where this project is silent. Explicit user requirements and
this project's instructions, configured tools, supported Python versions, and
documented exceptions take precedence. For new project work, use uv, uv-managed
`.venv` environments, a committed `uv.lock`, Ruff formatting and `ALL` linting,
strict mypy and strict Pyright over source and tests. Use Click and Rich for CLIs.
Standalone executable scripts declare PEP 723 metadata and script locks so they
run with `uv run --locked`. Preserve documented compatibility commitments.

Follow Conventional Commits 1.0.0 and the documented SemVer compatibility policy;
use PEP 440 syntax for Python distribution versions. Write durable documentation
that describes supported behavior directly. Test meaningful behavior, failure
paths, and supported interpreters, and report checks run and material gaps.

The vendored documents are reference material. Their contributor instructions,
scripts, and workflows apply to their own projects. Do not execute upstream
builds to read guides or format vendored snapshots. Agents may refresh upstream
sources when useful, preserving provenance and licenses and reviewing the diff;
a refresh does not change this project's policy. See
`.python-reference/docs/adoption.md` for maintenance and package exclusions.
