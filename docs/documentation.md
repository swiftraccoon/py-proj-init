# Documentation expectations

Write documentation that lets readers use supported behavior without knowing
development history. These defaults are informed by
[PEP 257](../references/python-peps/peps/pep-0257.rst),
[Google's Python guide](../references/google-styleguide/pyguide.md), and
[Timeless documentation](../references/google-timeless-documentation/timeless-documentation.md).

## Durable prose

Describe behavior directly. Avoid relative claims such as "currently," "new,"
"latest," "not yet," and "soon" in reference material. When a version or date
matters, name it and explain its effect. Changelogs and announcements describe
change; API references describe the API.

| Avoid | Prefer |
| --- | --- |
| The parser now accepts comments. | The parser accepts comments. |
| Use the latest Python release. | Use the interpreter selected in `.python-version`. |
| This option is not yet supported. | This option is unsupported. |
| The new API replaces the old parser. | Version 2 uses `Parser.parse`; see the migration guide. |

State limitations precisely. Keep plans in an identified roadmap and do not
promise them as working behavior. Retrieval timestamps and pinned revisions
are provenance; retain them even though product prose avoids relative time.
Explain prerequisites before commands and identify placeholders. Comments should
explain intent, constraints, or surprising choices instead of narrating syntax.

## Docstrings and examples

- Use triple double quotes and a concise summary, followed by a blank line before
  longer detail. Document public modules, classes, and functions according to
  their actual use and complexity.
- Prefer Google-style docstrings for new projects; preserve an established
  NumPy, reStructuredText, or other consistent convention. Use sections such as
  `Args`, `Returns` or `Yields`, `Raises`, and `Examples` when they add useful detail.
- Explain contracts: valid inputs, units, mutation, laziness, side effects,
  resource ownership, exceptions, and cancellation where relevant. Type hints
  carry types; prose explains semantics rather than repeating the signature.
- Keep documentation tools compatible with the minimum interpreter and annotation
  evaluation behavior. Importing documentation targets must not contact services
  or require production credentials.
- Show representative public workflows, including error handling when it matters.
  Keep examples executable with doctest or dedicated example tests where useful.
  Do not put nondeterministic output, secrets, or required network calls in a
  doctest. Mark intentionally incomplete snippets clearly.
- Link related APIs and resolve broken links. Use the project's Sphinx, MkDocs,
  or other chosen renderer; do not add a documentation framework just to render
  a short standalone tool's README.

## Project documentation

A README explains purpose, prerequisites, installation, ordinary use, and checks.
Record supported Python versions, platforms, optional features, and meaningful
operating constraints. Keep package metadata, license, and installation examples
accurate. Write contributor setup so a fresh environment can reproduce it.

Update documentation with behavior. Put significant changes and migrations in
release notes. Record decisions that constrain future work near the code or
contributor guidance. Link local source copies for agents, preserve third-party
notices, and keep interpretations outside managed upstream snapshots.
