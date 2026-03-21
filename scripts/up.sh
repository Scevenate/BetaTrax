#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py runserver