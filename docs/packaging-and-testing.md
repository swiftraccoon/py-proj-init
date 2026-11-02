# Packaging and testing

Use the local [Python Packaging User Guide](../references/python-packaging/source/index.rst)
and [pyproject guide](../references/python-packaging/source/guides/writing-pyproject-toml.rst)
for the complete instructions. These defaults leave the consuming project's
established tools and compatibility commitments intact.

## Project shape and metadata

Use `pyproject.toml` as the shared configuration entry point. Installable projects
declare a build backend in `[build-system]` and standard metadata in `[project]`.
Choose one maintained backend; preserve an existing backend during unrelated
work. A reference library or standalone script does not need a distribution build
just to store tool configuration.

Record the distribution name, version strategy, description, README, Python
requirement, license, and relevant project URLs. Choose an SPDX license expression
and matching license files with a backend that supports the corresponding metadata.
Keep distribution names distinct from import package names: `example-project`
can provide `example_project`. Define console entry points in `[project.scripts]`
and optional runtime integrations in `[project.optional-dependencies]`.

Prefer a `src/` layout for packages so tests do not accidentally import an
uninstalled working-directory copy. Install the package into the test environment.
Use an editable install for development and test an ordinary wheel installation
before release. Keep version information in one authoritative place; build tools
can derive metadata without importing application code with side effects.

## Requirements, groups, and locks

Put runtime dependencies in `project.dependencies`, with version bounds justified
by supported behavior. A library's requirements describe the versions its users
can resolve; avoid pinning every transitive dependency in published library
metadata. Test meaningful lower bounds as well as the ordinary resolution.

Use dependency groups for local testing and quality tools when the environment
manager supports them. Groups are not published runtime extras. Application and
development environments should use the project's lock format and commit the
lockfile. A library can lock its development environment while publishing broader
runtime requirements. Use frozen or locked installs in CI and review lock updates.
Do not claim a lock guarantees bit-for-bit reproducible builds across platforms.

Use uv as the project manager. `uv sync` creates and synchronizes `.venv/`;
`uv run` executes commands in that environment. Use `uv add` and dependency
groups to maintain declarations and `uv.lock`. Commit the lockfile and interpreter
pin. CI and ordinary validation use `--locked`; a lock update is a deliberate
change. Use the [strict tooling profile](tooling.md) and adapt the
[starter configuration](../templates/pyproject.toml). An explicitly established
project exception must explain an alternative manager or quality gate.

## Tests and quality checks

Use pytest with strict configuration, strict markers, and warnings as errors for
new projects. The maintenance pack retains its unittest integration suite and
runs it through uv with warnings as errors. Test observable behavior,
boundaries, errors, resource cleanup, and regressions. Use temporary directories
and deterministic fixtures. Mock external boundaries where appropriate, while
retaining integration coverage for the behavior that those mocks would hide.
Unit tests should run without network access, user credentials, or global state.

Configure Ruff `ALL`, strict mypy, and strict Pyright to the declared minimum
Python version. Check source, tests, and project-owned scripts. For a package:

```sh
uv sync --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src tests
uv run --locked pyright
uv run --locked pytest
uv build
uv run --locked twine check dist/*
```

Declare the tools in dependency groups and configure the backend before using
these commands. `uv sync` installs the locked environment. `twine check` checks distribution metadata and README rendering;
it does not upload a package or replace artifact installation tests.

Use coverage to find untested meaningful paths. Avoid adding tests that merely
repeat implementation details or assert an arbitrary percentage. Keep tests
independent, run them from more than one working directory where path behavior
matters, and verify platform-specific behavior on that platform.

## CI and release artifacts

Test the minimum supported interpreter and each promised minor version. Include
the operating systems, alternative interpreters, extras, and extension builds
that the project supports. A small tool may use the full version range on Linux
and the oldest and development interpreters on macOS and Windows. Quality tools
can run once on a fixed development interpreter.

Use minimal CI permissions, pin third-party actions to reviewed commits, and
separate ordinary checks from publication. Keep builds free of credentials.
Run documented security or dependency audits when relevant to the project and
review findings in context; do not silently ignore failures.

Before releasing, build both a wheel and sdist in a clean output directory.
Inspect their contents and license files. Install the wheel into a clean
environment, run its public workflow, then build and test from the sdist. Include
type markers, package data, and required runtime resources; exclude credentials,
virtual environments, caches, and `.python-reference/`. Configure exclusions for
the actual backend rather than assuming `.gitignore` controls every build.

Publishing follows the project's explicit authorization and release workflow.
Trusted Publishing can avoid long-lived PyPI credentials when supported. A
reference pack provides policy; it does not configure or trigger publication.
