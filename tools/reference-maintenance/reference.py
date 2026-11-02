#!/usr/bin/env -S uv run --script --locked
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.3,<9", "rich>=14,<15"]
# ///
# Copyright (C) 2026 Python project reference contributors
# SPDX-License-Identifier: 0BSD
"""Run the Click and Rich maintenance CLI with uv-managed dependencies."""

from reference_maintenance.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
