# Strict tooling profile

This is the default stack for projects adopting this pack. Apply it to new
projects and new standalone tools; record an existing project's intentional
exceptions with their scope and reason. The pack's own tooling follows this
profile and checks its source and integration tests.

## uv owns the environment

Use uv for Python selection, dependency declarations, resolution, virtual
environments, scripts, builds, and command execution. Use a project-local `.venv/`;
`uv sync` creates it and `uv venv` creates an explicit environment when needed.
Keep `.venv/` out of version control. Do not depend on shell activation or globally
installed Python packages.

Commit `pyproject.toml`, `uv.lock`, and `.python-version`. Use `uv add` and
`uv add --dev` for dependency changes and review the resulting lock diff. Use
`uv sync --locked` and `uv run --locked` for ordinary checks and CI; a stale lock
must fail instead of resolving a different environment. Update the lock
deliberately. Pin uv itself in CI. Avoid mixing uv with Poetry, pip-tools, or
manual pip installs into the same managed environment.

Use Python 3.14 as the starter development interpreter and compatibility floor
unless the project has a concrete need for another supported version. Record
that decision and align Ruff, mypy, Pyright, and CI with it. The reference
maintenance tools deliberately support Python 3.11–3.15 for adoption by older
projects while developing on 3.14.

For an installable package, a starting workflow is:

```sh
uv init --package --build-backend hatch --python 3.14 example-project
cd example-project
uv python pin 3.14
# Merge templates/pyproject.toml from this pack, adjusting package metadata.
uv sync
# Commit pyproject.toml, .python-version, and uv.lock after reviewing them.
```

The [starter pyproject](../templates/pyproject.toml) uses Hatchling for a pure
Python package. Keep an established backend when adopting the quality profile.
The maintenance reference project is not a distributable package and uses
`tool.uv.package = false`.

## Standalone scripts

Executable scripts use [PEP 723 inline metadata](../references/python-peps/peps/pep-0723.rst)
to declare their interpreter requirement and direct dependencies. For example:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["click>=8.3,<9", "rich>=14,<15"]
# ///
```

Create metadata with `uv init --script example.py --python 3.14` or maintain it
in the script header. Add dependencies with `uv add --script example.py ...`.
Run `uv lock --script example.py` and commit `example.py.lock`; execute it with
`uv run --locked example.py`. Use a uv shebang when direct execution is useful:
`#!/usr/bin/env -S uv run --script --locked`.

Declare an empty dependency list for a standard-library-only executable script.
Do not add script metadata to importable library modules, package entry-point
modules, or test files. Project scripts and dependency-bearing standalone scripts
have different environments: inline metadata does not inherit undeclared project
dependencies. Keep shared dependency constraints consistent and lock both entry
points if a tool supports both forms.

The [Click/Rich script template](../templates/cli_script.py) runs directly:

```sh
uv run --locked templates/cli_script.py --name Ada
```

The first run can install dependencies or an interpreter. Use `--offline` only
after the required artifacts are cached. Reading the reference documents still
requires no Python or uv.

## Click and Rich for CLIs

Use Click for options, arguments, validation, help, nested commands, and exit
behavior. Use Rich `Console` objects for human-readable results and diagnostics,
with errors directed to stderr. Keep the command layer small and domain behavior
callable independently from the terminal. Do not build a parallel manual argument
parser or use a different CLI framework without a documented requirement.

Treat user input as data: disable Rich markup for arbitrary paths, source names,
and exception text, or render escaped `Text`. Preserve normal pipe and redirected
output behavior. Machine-readable output must be stable and free of spinners or
color codes. Validate through Click parameter types and domain boundaries;
handle expected failures with useful messages and meaningful nonzero exit codes.
Exercise public command behavior with Click's testing helpers or subprocess tests.

## Quality gates

| Gate | Required profile |
| --- | --- |
| Formatting | Ruff format, four spaces, 88 columns |
| Lint | Ruff `select = ["ALL"]`, including security, annotations, documentation, complexity, imports, and correctness rules |
| Type checking | mypy `strict = true`, unreachable-code checks, no explicit or unresolved `Any`, and ignores with error codes |
| Independent type analysis | Pyright `typeCheckingMode = "strict"`, unnecessary ignores reported as errors |
| Tests | pytest strict config/markers, importlib import mode, warnings as errors, deterministic behavioral tests |

Run checks on all project-owned source, tests, and scripts. Keep code within the
tools' configured complexity limits; split responsibilities instead of raising
thresholds to fit a large function. Fix inferred unknown types at boundaries.
Do not use blanket `type: ignore`, `noqa`, broad per-file exclusions, or
`ignore_missing_imports = true` to achieve a passing check.

Ruff's full rule set includes mutually exclusive style choices and rules that
overlap the formatter. Select Google docstring conventions and leave trailing
commas to the formatter (`COM812` is disabled). Other exceptions need a specific
code, smallest practical scope, and an explanation. The maintenance tests retain
unittest; their per-file exceptions permit unittest assertions, descriptive test
names in place of method docstrings, and numeric fixture expectations. Security
exceptions at subprocess and HTTPS calls identify their actual validation boundary.
These exceptions are not a general exemption for production code.

Lock quality tool versions and review new findings when upgrading them. `ALL`
can gain rules when Ruff changes; resolve them as part of that tool update.
Require clean Ruff, mypy, Pyright, and test results in CI. Do not downgrade a
check to advisory status or hide a failure behind a successful shell exit.

The maintenance project uses the same strict checks with a unittest integration
suite and `python -W error`. See its [development commands](../tools/reference-maintenance/README.md).

## Tool references

Use the maintained tool documentation for command details:
[uv scripts](https://docs.astral.sh/uv/guides/scripts/),
[Ruff rule selection](https://docs.astral.sh/ruff/linter/#rule-selection),
[mypy configuration](https://mypy.readthedocs.io/en/stable/config_file.html),
[Pyright configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md),
[Click](https://click.palletsprojects.com/en/stable/), and
[Rich Console](https://rich.readthedocs.io/en/stable/console.html).
These tool manuals are online; the language, packaging, typing, and shared
project references are stored locally in this pack.
