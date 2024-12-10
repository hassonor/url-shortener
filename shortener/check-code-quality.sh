#!/usr/bin/env bash

EXIT_STATUS=0

# If a virtual environment exists, activate it
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

exit $EXIT_STATUS