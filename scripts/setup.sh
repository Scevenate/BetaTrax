#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
uv sync
uv run manage.py makemigrations BetaTrax
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py createsuperuser