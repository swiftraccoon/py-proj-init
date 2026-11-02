# Adopt and maintain the reference

## Export a self-contained pack

With an existing Python project as the destination, run from this repository:

```sh
uv run --locked tools/reference-maintenance/reference.py export /absolute/path/to/python-project
```

The exporter creates `.python-reference/` containing guidance, upstream snapshots,
provenance, licenses, templates, and the maintenance project. It omits
Git metadata, virtual environments, bytecode, build output, and caches from our
tooling. Upstream tracked content is copied verbatim, including files that would
normally look like build configuration. Sources are checked before and after
copying. An existing pack, including a dangling symlink, is never overwritten.
The destination must exist and be outside the source pack.

Merge `.python-reference/templates/AGENTS.md` into the project's root `AGENTS.md`.
If the file is absent, copy the template there. A nested reference pack alone
does not direct agents working elsewhere in the consuming project. The exporter
leaves existing project instructions, Python configuration, and source files alone.

Commit the pack when every checkout needs offline access. Resolve any Git ignore
warnings before committing: a broad rule such as `docs/` or `*.rst` can exclude
part of the pack. Preserve the pack's `.gitattributes` so Git does not change
snapshot line endings on Windows or checkouts using `core.autocrlf=true`.
Do not apply formatters or line-ending normalization to upstream documents.

Authored policy, tools, and templates use [0BSD](../LICENSE). Upstream sources
retain their own licenses and attribution, including the Packaging User Guide's
share-alike terms. Keep snapshots, notices, and provenance together. See the
[license inventory](../references/README.md#licenses-and-attribution).

## Keep references outside published artifacts

The consuming project owns its packaging configuration. Exclude
`.python-reference/` from wheels and sdists with that backend's supported options,
then inspect the actual artifacts. A `.gitignore` rule alone is not a portable
build exclusion policy. A `src/` layout helps keep unrelated root content out of
the wheel, but the sdist needs review too. For example, a project already using
Hatchling can add the following to its existing exclusions:

```toml
[tool.hatch.build]
exclude = ["/.python-reference"]
```

Merge with the project's existing table rather than replacing it. Use the
equivalent documented setting for other backends. Do not change backend just to
copy this example. Publishing a package does not require distributing its local
reference library.

The maintenance project is nested under `tools/`. Its `pyproject.toml`, project
and script lockfiles, and interpreter pin are independent of the consuming project's configuration.
Do not automatically add it as a workspace member or runtime dependency.

## Use a shared checkout

The pack can stay beside projects. Add a concrete absolute path to each consuming
project's root agent guidance, for example:

```markdown
## Python references

Read `/absolute/path/to/py-proj-init/docs/python-expectations.md`,
`packaging-and-testing.md`, `documentation.md`, and `commits-and-releases.md`.
Resolve those filenames within the same `docs/` directory.
Use `/absolute/path/to/py-proj-init/references/README.md` for full local sources.
These defaults yield to this project's explicit requirements and configuration.
```

Replace the example path before use. This approach needs access to that checkout;
an exported, committed pack is self-contained for other machines.

## Verify and refresh

Use uv; it provisions the CLI's Click and Rich dependencies and a compatible
Python interpreter. Refreshes of Git sources additionally need Git. Commands below
run from the pack root, including an exported pack's root:

```sh
# Read-only source verification; uv needs cached dependencies for offline use.
uv run --locked tools/reference-maintenance/reference.py sync --check

# Fetch the configured upstream branch heads and web page.
uv run --locked tools/reference-maintenance/reference.py sync

# Refresh only selected sources.
uv run --locked tools/reference-maintenance/reference.py sync python-peps google-styleguide

# Recreate missing files from exactly the recorded revisions.
uv run --locked tools/reference-maintenance/reference.py sync --locked

# Deliberately discard edits to a selected managed snapshot.
uv run --locked tools/reference-maintenance/reference.py sync --locked --force python-peps
```

The CLI detects missing, added, and edited files and checks acquisition metadata
against the source definitions. Normal refreshes refuse to replace local snapshot
changes unless `--force` is supplied. A locked restore can recreate missing files
without `--force`, but still protects edits and additions. Force applies only to
selected source snapshots; it does not override an export destination or unsafe
reference/cache directory layout.

A locked restore requires matching source configuration and an existing manifest.
It preserves the recorded revision, retrieval time, transformations, and hashes.
Matching sources are untouched. Git commits are fetched by exact hash only if
absent from the cache; a deleted branch does not prevent restoring a reachable
recorded commit. Git objects are read without checkout filters, so user settings
and upstream `export-ignore` attributes do not change snapshot bytes.

Web pages have no immutable revision endpoint. The timeless article can be
restored only from the exact recorded HTML still in the snapshot or its local
content-addressed cache. If unavailable, restore the committed snapshot from
Git or run a normal refresh to accept the changed page. A locked restore never
substitutes a newer web page. Derived reading copies must also match their hashes.

Review `git diff` after an update, including licenses, manifest revisions, and
transformation descriptions. The maintained PyPA and typing specifications can
supersede historical PEP details; the relevant local sources and the consuming
project's supported tools determine applicability. A refresh does not authorize
an interpreter migration or change project policy.

## Failure handling and recovery

Refreshes stage all selected sources before replacing any snapshot. Installation
backs up the previous source directories and replaces the manifest atomically.
If an installation operation fails, the tool attempts to restore every previous
snapshot. If rollback fails, it retains `.reference-sync-*` with recovery files
and reports their location. Inspect and recover these files before another sync;
unmanaged leftovers are rejected by integrity checks and exports.

This rollback handles ordinary operation failures; a process kill or power loss
can interrupt a multi-directory transaction. Recover the affected snapshots and
manifest together from version control or the retained backups, then run
`sync --check`. A `.reference-maintenance.lock` excludes concurrent refresh
writers. Remove a stale lock only after confirming the original process stopped.

Upstream symlinks are materialized as regular files only when their file targets
are present within the selection. Escaping, dangling, and cyclic links fail.
Snapshot symlinks, devices, and FIFOs fail verification. Finder/Explorer metadata
is ignored. Exported maintenance tools retain their Python source and tests,
but virtual environments and interpreter caches are omitted.

The exported scripts carry PEP 723 dependency headers and adjacent lockfiles.
Run them with `uv run --locked`; uv provisions Click and Rich in isolated script
environments. Use `uv run --offline --locked` when the required interpreter and
dependencies are cached. See [the strict tooling profile](tooling.md) for the
package configuration, CLI conventions, and quality gates.
