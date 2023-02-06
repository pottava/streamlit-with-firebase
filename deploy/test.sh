#!/bin/sh

set -e

cd src
pip install poetry
poetry install --no-interaction --no-ansi
poetry run isort .
poetry run black .
poetry run flake8 --exclude=.venv .
poetry run pip-audit
