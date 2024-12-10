#!/usr/bin/env bash

set -e

# Activate virtual environment if present
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
fi

echo "Running isort..."
isort .

echo "Running black..."
black .

echo "Running ruff..."
ruff check . --fix

echo "All code quality checks passed!"
