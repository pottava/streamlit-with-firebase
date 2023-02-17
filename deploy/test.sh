#!/bin/sh

cd src
pip install poetry
poetry install --no-interaction --no-ansi --no-root

set -e
poetry run isort .
poetry run black .
poetry run flake8 --exclude=.venv .
poetry run pip-audit
