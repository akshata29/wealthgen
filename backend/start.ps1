# WealthGen backend launcher — creates/activates .venv, installs deps, runs Uvicorn.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Warning ".env not found. Copy .env.example to .env and populate before running."
}

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
