#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
uv run manage.py test tests/