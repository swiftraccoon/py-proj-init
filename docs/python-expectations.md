# Python project expectations

These defaults combine the local guides with practical project conventions.
They are our policies, not a claim that every upstream source requires each rule.
Explicit user requirements and the consuming project's documented choices take
precedence. Record departures that affect later work in that project's guidance.

Read [PEP 8](../references/python-peps/peps/pep-0008.rst),
[Google's Python guide](../references/google-styleguide/pyguide.md), and the
[typing specification](../references/python-typing/docs/spec/index.rst) for detail.
See [packaging and testing](packaging-and-testing.md) for build and validation policy.

## Interpreter, environments, and formatting

- Use a supported Python 3 release. Choose and document the minimum interpreter
  and supported implementations and platforms. An existing project's promises
  determine usable syntax and standard-library APIs.
- Put a distribution's minimum version in `project.requires-python`. A local
  `.python-version` selects a development interpreter; it is a separate choice
  from the compatibility floor. Test the floor and supported versions in CI.
- Use uv for interpreter selection, dependency management, virtual environments,
  scripts, builds, and tool execution. Keep the project environment in `.venv/`,
  created by `uv sync` or `uv venv`. Commit `uv.lock` and `.python-version` and
  run commands through `uv run`. CI uses locked resolution.
- Implement project-owned automation in Python when practical. Prefer the
  standard library when it meets the requirement; a shell wrapper can launch
  tools when it does not need application logic.
- Use Ruff formatting and all applicable lint rules (`select = ["ALL"]`), four
  spaces, and an 88-column code width. PEP 8 uses
  79 columns and Google uses 80; our width is an explicit formatter choice.
  Keep prose readable at roughly 72–88 columns.
- Keep formatter settings and supported Python targets in `pyproject.toml`.
  Lock development tools with uv. Require strict mypy and strict Pyright with
  zero diagnostics, including tests. Do not reformat
  unrelated code or vendored references during a behavior change.

## Layout, names, and imports

Use `src/<import_package>/` for installable packages and `tests/` for tests.
A focused standalone maintenance script can use a flat layout. Keep entry points
small: parse configuration, call application code, translate errors to useful
messages and exit codes. Use Click for parsing, validation, help, and commands,
and Rich for terminal output. Executable scripts declare PEP 723 metadata and
their dependencies so they run with `uv run`; lock script dependencies as well.
See [tooling](tooling.md) for the complete profile. Importing a package must not run a CLI, contact a service,
configure global logging, or modify the filesystem.

Use `snake_case` for modules, functions, and variables, `CapWords` for classes,
and `UPPER_CASE` for constants. Mark internal APIs with a leading underscore;
document the supported public surface. Avoid wildcard imports, `sys.path` hacks
in application code, and names that shadow built-ins. Group standard-library,
third-party, and local imports. Use absolute imports by default, with explicit
relative imports where they clarify an internal package relationship.

Organize modules around responsibilities, with dependencies flowing toward core
behavior. Avoid circular imports, mutable global registries, and frameworks for
private helpers that do not need them. Prefer composition and ordinary functions
to inheritance and metaprogramming unless the domain benefits from those choices.

## APIs, data, and typing

Annotate all project-owned functions, including test helpers. Run mypy and
Pyright in strict mode over source, scripts, and tests. Existing projects can
adopt the profile in an explicitly documented scope. Prefer precise types to
unbounded `Any`; narrow dynamic data at boundaries. Type annotations do not
validate untrusted input at runtime.

Use built-in generics and union syntax when the minimum interpreter supports
them. Use `collections.abc` interfaces for inputs when callers need flexibility,
and concrete return types when they communicate useful guarantees. Choose
`Protocol`, generics, `TypedDict`, enums, or dataclasses to express real contracts,
not to add abstraction to simple code. `typing_extensions` is appropriate when
the compatibility floor requires a backport. Do not adopt syntax from an evolving
typing specification before the selected interpreter and checker support it.

Avoid mutable default arguments and hidden shared state. Use explicit `None`
checks when `0`, `False`, or an empty collection is a valid value. Define whether
functions mutate input, consume an iterator, own a resource, or return a lazy
result. Keep public parameter names, defaults, exception types, and return
semantics compatible with documented callers. Make deprecations and migrations
visible. Typed libraries should ship and test their `py.typed` marker as described
in [PEP 561](../references/python-peps/peps/pep-0561.rst).

## Exceptions and resources

Raise specific exceptions for failures; return `None` for an expected absence
when no diagnostic is needed. Catch only exceptions the code can handle. Keep
the `try` block narrow, preserve causes with `raise ... from exc` when translating
errors, and include the operation and relevant safe input in boundary diagnostics.
Do not swallow failures or return success for incomplete work. Assertions check
programmer invariants, not user input: optimized Python can remove them.

Catch broad `Exception` only at a deliberate application boundary for reporting,
cleanup, or rollback, and preserve failure. Do not catch `BaseException` in normal
error handling. Keep CLI cancellation and exit behavior deliberate. Libraries
should expose exceptions instead of exiting the process.

Use context managers for files, locks, transactions, and temporary resources.
Specify text encodings, keep binary data binary, and use `pathlib` for paths.
Account for missing files, permissions, partial writes, and platform differences.
Stage important replacements and use atomic file replacement when supported;
document recovery for operations spanning several files. Avoid changing process
working directories or environment variables as a hidden library side effect.

## Security, concurrency, and performance

Validate external data at the boundary, including size and structure where the
application requires it. Use argument lists for subprocesses and parameterized
database queries. Avoid `shell=True`, `eval`, and untrusted pickle input. Use
`secrets` for security tokens and keep credentials and personal data out of logs.
Network clients need explicit timeouts and deliberate retry behavior.

Use concurrency when the workload needs it. Choose synchronous code, threads,
processes, or async based on actual I/O and CPU constraints. Define cancellation,
shutdown, task ownership, and synchronization. Avoid blocking an event loop or
holding locks across awaits. Do not rely on the GIL to protect compound state,
or assume interpreter builds share the same threading behavior.

Measure before optimizing. Use representative inputs and keep correctness and
resource bounds visible. Introduce native extensions or additional runtimes only
when justified by requirements and maintenance cost.

## Dependencies and delivery

Before adding a dependency, assess its purpose, maintenance, license, interpreter
and platform support, transitive cost, and overlap with existing dependencies.
Keep runtime dependencies separate from development tools. Declare every direct
dependency rather than relying on an incidental transitive installation.

Run documented checks, add meaningful behavioral tests, and update documentation
with the code it describes. Lint and typing suppressions need the smallest useful
scope and a reason. Deliver changes with checks run and any material gaps.
See [documentation](documentation.md) and [release policy](commits-and-releases.md).
