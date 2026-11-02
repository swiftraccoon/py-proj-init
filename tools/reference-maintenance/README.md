# Reference maintenance

This independent uv project maintains the checked-in reference library. Its
Click commands and Rich output work through either the locked project environment
or PEP 723 script environments. Source code and tests support Python 3.11–3.15;
development uses Python 3.14. Git is required for source acquisition and local
integration fixtures. No bundled upstream code or website build is executed.

From the pack root:

```sh
uv run --locked tools/reference-maintenance/reference.py --help
uv run --locked tools/reference-maintenance/reference.py sync --check
uv run --locked tools/reference-maintenance/check_docs.py
```

`--root PATH` before the subcommand selects another pack. Otherwise the root is
derived from the script location, independently of the working directory.
Each entry point declares Click and Rich in its inline metadata and has an
adjacent script lockfile. uv provisions its environment; a direct Unix invocation
uses the uv shebang too. Keep the project and script dependency constraints aligned.

The first run can install dependencies or Python. With those artifacts cached,
add `--offline` to uv for source checks and exports. A normal refresh needs Git
and HTTPS. `sync --locked` fetches only missing recorded Git commits and never
substitutes a changed web page. See [adoption and recovery](../../docs/adoption.md).

## Development and quality checks

`uv sync` creates `.venv/` in this directory. Commit `uv.lock` and `.python-version`;
CI and ordinary checks use locked resolution. From the pack root:

```sh
uv sync --project tools/reference-maintenance --locked
uv run --project tools/reference-maintenance --locked python -W error -m unittest discover -s tools/reference-maintenance/tests -t tools/reference-maintenance -v
uv run --project tools/reference-maintenance --locked ruff format --check tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked ruff check tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked mypy --config-file tools/reference-maintenance/pyproject.toml tools/reference-maintenance templates/cli_script.py
uv run --project tools/reference-maintenance --locked pyright --project tools/reference-maintenance/pyproject.toml
```

Ruff enables `ALL` with Google docstrings and formatter-compatible trailing comma
policy. mypy and Pyright both run in strict mode over production code and tests.
Exceptions are narrow, documented in configuration or at the affected call, and
covered by behavior tests. The unittest suite runs with warnings as errors and
uses temporary local Git repositories rather than network services.

CI exercises Python 3.11–3.15 on Linux and the compatibility floor and development
interpreter on macOS and Windows. Its test jobs use isolated uv environments,
leaving the project's development interpreter selection intact. Formatting and
type checks run on Python 3.14.

Update runtime dependencies deliberately with uv, then regenerate script locks:

```sh
uv lock --project tools/reference-maintenance
uv lock --script tools/reference-maintenance/reference.py
uv lock --script tools/reference-maintenance/check_docs.py
```

Source configuration lives in `reference_maintenance/sources.py`. A renamed
selected path fails acquisition instead of silently dropping a document or
license. Review source configuration changes alongside manifest and snapshot
diffs. Add interpretations to `docs/`, preserving managed upstream bytes.
