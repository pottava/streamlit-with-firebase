#!/bin/sh

cd src
pip install poetry
poetry install --no-interaction --without dev --no-ansi
poetry run isort .
poetry run black .
poetry run flake8 --exclude=.venv .
poetry run pip-audit
poetry export --without-hashes --format=requirements.txt > requirements.txt
