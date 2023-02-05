#!/bin/sh

set -e

cd src
pip install poetry
poetry install --no-interaction
poetry run isort .
poetry run black .
poetry run flake8 --exclude=.venv .
poetry run pip-audit
poetry export --without dev --without-hashes --format=requirements.txt > requirements.txt
