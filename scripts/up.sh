#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
uv sync
uv run manage.py runserver