@echo off
REM ==========================================================================
REM WealthGen backend launcher
REM Creates/activates .venv, installs deps, and runs the FastAPI app (Uvicorn).
REM ==========================================================================
setlocal
cd /d "%~dp0backend"

if exist ".venv" goto :activate

echo Creating virtual environment .venv and installing dependencies (first run)...
python -m venv .venv
if errorlevel 1 goto :error
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error
goto :check_env

:activate
call ".venv\Scripts\activate.bat"

:check_env
if exist ".env" goto :run
echo.
echo WARNING: backend\.env not found. Copy .env.example to .env and populate it
echo          before the app can reach Azure services.
echo.

:run
echo Starting WealthGen backend on http://localhost:8000 ...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto :eof

:error
echo.
echo Backend launch failed. See the messages above.
exit /b 1
