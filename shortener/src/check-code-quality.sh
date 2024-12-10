# check-code-quality.ps1

# Ensure the script stops if any command fails
$ErrorActionPreference = "Stop"

# Function to display messages in different colors
function Write-Color {
    param (
        [string]$Message,
        [ConsoleColor]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Activate the virtual environment if not already activated
if (-not ($env:VIRTUAL_ENV)) {
    $venvPath = ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        Write-Color "Activating virtual environment..." -Color Cyan
        . $venvPath
        Write-Color "Virtual environment activated." -Color Green
    } else {
        Write-Color "Warning: Virtual environment not found. Proceeding without activation." -Color Yellow
    }
}

# Run isort to sort imports
Write-Color "Running isort to sort imports..." -Color Cyan
isort src/
Write-Color "isort completed successfully." -Color Green

# Run Black to format code
Write-Color "Running Black to format code..." -Color Cyan
black src/
Write-Color "Black completed successfully." -Color Green

# Run Ruff to lint and fix code
Write-Color "Running Ruff to lint and fix code..." -Color Cyan
ruff check src/ --fix
Write-Color "Ruff completed successfully." -Color Green

Write-Color "All code quality checks passed successfully!" -Color Green
