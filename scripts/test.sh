#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
uv sync
uv run ruff check || exit 1
uv run manage.py test tests/ || exit 1