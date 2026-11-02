#!/usr/bin/env -S uv run --script --locked
# /// script
# requires-python = ">=3.14"
# dependencies = ["click>=8.3,<9", "rich>=14,<15"]
# ///
# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""A runnable Click and Rich starting point for a standalone uv script."""

import click
from rich.console import Console


@click.command()
@click.option("--name", default="world", show_default=True, help="Person to greet.")
def main(name: str) -> None:
    """Greet NAME using a uv-provisioned Click and Rich environment."""
    Console(markup=False, highlight=False).print(f"Hello, {name}!", style="green")


if __name__ == "__main__":
    main()
