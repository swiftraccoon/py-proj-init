# Commits and releases

Use [Conventional Commits 1.0.0](../references/conventional-commits/content/v1.0.0/index.md)
and [Semantic Versioning 2.0.0](../references/semver/spec/v2.0.0.md) for change intent
and compatibility policy. Python distribution metadata and dependency comparisons
follow [PEP 440](../references/python-peps/peps/pep-0440.rst) and the maintained
[version specification](../references/python-packaging/source/specifications/version-specifiers.rst).
These systems serve different purposes; do not feed arbitrary SemVer strings
directly into Python packaging metadata.

## Commit messages

```text
type(optional-scope)!: concise description

Optional body explaining the reason and relevant behavior.

BREAKING CHANGE: describe the incompatible change and migration.
```

Scope, `!`, body, and footers are optional. Mark breaking changes with `!` just
before the colon or a `BREAKING CHANGE:` footer; prefer both a visible marker
and migration details when users are affected. Lowercase types and scopes and
an imperative description without a final period are house style beyond the spec.

| Type | Use |
| --- | --- |
| `feat` | Public capability or API addition |
| `fix` | Correct incorrect behavior |
| `docs` | Documentation |
| `refactor` | Restructure without a feature or bug fix |
| `perf` | Performance improvement |
| `test` | Tests or test infrastructure |
| `build` | Dependencies, backend, interpreter settings, or build tooling |
| `ci` | CI configuration |
| `style` | Formatting without behavior changes |
| `chore` | Other maintenance, including reference refreshes |
| `revert` | Revert a commit identified in the body or footer |

`feat` and `fix` have specified meanings; the other types are our conventions
and do not automatically require a version bump unless compatibility changes.
Dropping a supported interpreter can need a breaking marker even under `build`.

```text
fix(parser): reject truncated input
docs: explain retry behavior
chore(references): refresh Python packaging guidance
feat(config)!: require explicit storage paths

BREAKING CHANGE: pass storage_path instead of relying on the working directory.
```

Keep commits coherent. For squash merging, ensure the final message captures the
whole change and its breaking status. Do not rewrite published history to adjust
messages. This convention does not itself configure automated releases.

## Compatibility and version policy

Document the public surface: import paths, public names, parameter names and
defaults, return types and semantics, exceptions, CLI arguments and exit codes,
configuration, data formats, and supported interpreters and platforms. Type hints
are part of the contract for a typed library; narrowing accepted types or changing
protocol requirements can break callers even if runtime code still executes.

For stable releases (`1.0.0` and above):

| Change | Bump | Example |
| --- | --- | --- |
| Compatible fix | Patch | `1.4.2` → `1.4.3` |
| Compatible public functionality or deprecation | Minor | `1.4.2` → `1.5.0` |
| Incompatible public change | Major | `1.4.2` → `2.0.0` |

Choose the largest required bump in the release and reset lower components.
Review actual compatibility instead of relying only on commit labels. During
`0.y.z`, our default is compatible fixes in `0.y.(z+1)`, and new functionality or
incompatibilities in `0.(y+1).0`. This is a house policy, not a SemVer guarantee.
Still mark breaking commits and explain migration. Release `1.0.0` when ready
to make the documented stability commitment.

## Python distribution versions

Use PEP 440 spelling in `project.version` or backend-derived metadata:

| Intent | Python metadata | SemVer spelling for comparison |
| --- | --- | --- |
| Stable release | `2.0.0` | `2.0.0` |
| Alpha | `2.0.0a1` | `2.0.0-alpha.1` |
| Beta | `2.0.0b1` | `2.0.0-beta.1` |
| Release candidate | `2.0.0rc1` | `2.0.0-rc.1` |
| Development snapshot | `2.0.0.dev1` | No universal mapping |
| Post release | `2.0.0.post1` | No universal mapping |

The comparison column is illustrative, not a bidirectional conversion algorithm.
PEP 440 local labels (`+...`) are not SemVer build metadata and do affect Python
version ordering. Do not use them for ordinary public upstream releases. Never
replace published files under an existing version; publish a distinct version.
Do not use a post release to hide a behavioral patch that needs a patch version.

## Release review

- Review signatures, imports, exceptions, defaults, type information, entry points,
  extras, and documented behavior for compatibility.
- Review interpreter/platform changes and dependency bounds against the published
  support policy, and state their impact in release notes.
- Run the project's checks, build and inspect wheel and sdist, and test installation
  and public workflows from the artifacts in clean environments.
- Keep metadata, version source, tags, changelog, and migration instructions
  consistent. Git tags may use a `v` prefix; package metadata uses the version.
- Follow the project's release authorization and publication workflow. Choosing
  a commit format or version number does not authorize a package upload.
