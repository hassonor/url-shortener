#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Function to display messages in different colors
function write_color() {
    local message=$1
    local color=$2

    case $color in
        "green") echo -e "\033[0;32m${message}\033[0m" ;;
        "cyan") echo -e "\033[0;36m${message}\033[0m" ;;
        "yellow") echo -e "\033[0;33m${message}\033[0m" ;;
        "red") echo -e "\033[0;31m${message}\033[0m" ;;
        *) echo -e "${message}" ;;
    esac
}

# Activate the virtual environment if not already activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    venv_path=".venv/bin/activate"
    if [[ -f $venv_path ]]; then
        write_color "Activating virtual environment..." "cyan"
        source $venv_path
        write_color "Virtual environment activated." "green"
    else
        write_color "Warning: Virtual environment not found. Proceeding without activation." "yellow"
    fi
fi

# Run isort to sort imports
write_color "Running isort to sort imports..." "cyan"
isort src/
write_color "isort completed successfully." "green"

# Run Black to format code
write_color "Running Black to format code..." "cyan"
black src/
write_color "Black completed successfully." "green"

# Run Ruff to lint and fix code
write_color "Running Ruff to lint and fix code..." "cyan"
ruff check src/ --fix
write_color "Ruff completed successfully." "green"

write_color "All code quality checks passed successfully!" "green"
