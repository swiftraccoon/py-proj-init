# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Click commands and Rich diagnostics for the reference maintenance workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

from . import export, sync
from .model import MaintenanceError

if TYPE_CHECKING:
    from collections.abc import Sequence

CONSOLE = Console(markup=False, highlight=False)
ERROR_CONSOLE = Console(stderr=True, markup=False, highlight=False)


def reference_root() -> Path:
    """Resolve the pack containing this tool independently of its working directory."""
    return Path(__file__).resolve().parents[3]


@click.group(invoke_without_command=True)
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=reference_root,
    show_default="the reference pack containing this script",
    help="Reference pack root.",
)
@click.pass_context
def app(context: click.Context, root: Path) -> None:
    """Verify, refresh, or export the Python project reference library."""
    context.obj = root
    if context.invoked_subcommand is None:
        CONSOLE.print(context.get_help())


@app.command("sync")
@click.option(
    "--check", is_flag=True, help="Verify local snapshots without network or writes."
)
@click.option("--locked", is_flag=True, help="Restore the exact recorded snapshots.")
@click.option(
    "--force", is_flag=True, help="Replace local edits in selected snapshots."
)
@click.argument("sources", nargs=-1)
@click.pass_obj
def sync_command(
    root: Path, sources: tuple[str, ...], *, check: bool, locked: bool, force: bool
) -> None:
    """Refresh selected SOURCES, or all configured sources when omitted."""
    if check and locked:
        message = "Choose --check or --locked."
        raise click.UsageError(message)
    sync.run(
        root,
        sources,
        sync.Options(check=check, locked=locked, force=force),
        report=CONSOLE.print,
    )


@app.command("export")
@click.argument(
    "project", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.pass_obj
def export_command(root: Path, project: Path) -> None:
    """Copy a verified pack into an existing PROJECT directory."""
    result = export.run(root, project)
    CONSOLE.print(f"Reference pack copied to {result.destination}")
    CONSOLE.print(
        "Merge .python-reference/templates/AGENTS.md into the project's AGENTS.md."
    )
    if result.ignored_by_git:
        examples = ", ".join(result.ignored_by_git[:3])
        ERROR_CONSOLE.print(
            f"Warning: Git ignores {len(result.ignored_by_git)} pack file(s), "
            f"including {examples}. "
            "Adjust the project's ignore rules before committing.",
            style="yellow",
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Click application, translating expected failures to Rich diagnostics."""
    try:
        app.main(args=list(argv) if argv is not None else None, standalone_mode=False)
    except click.ClickException as exc:
        ERROR_CONSOLE.print(f"Error: {exc.format_message()}", style="red")
        return exc.exit_code
    except (MaintenanceError, OSError, ValueError, subprocess.SubprocessError) as exc:
        ERROR_CONSOLE.print(f"Reference maintenance failed: {exc}", style="red")
        return 1
    except (KeyboardInterrupt, click.Abort):
        ERROR_CONSOLE.print("Reference maintenance interrupted.", style="yellow")
        return 130
    return 0
