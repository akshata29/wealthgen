@echo off
REM ==========================================================================
REM WealthGen frontend launcher
REM Installs npm dependencies (first run) and starts the Vite dev server.
REM Vite proxies /api to the backend at http://localhost:8000.
REM ==========================================================================
setlocal
cd /d "%~dp0frontend"

if exist "node_modules" goto :dev
echo Installing npm dependencies for the first run...
call npm install
if errorlevel 1 goto :error

:dev
echo Starting WealthGen frontend on http://localhost:5173 ...
call npm run dev
goto :eof

:error
echo.
echo Frontend launch failed. See the messages above.
exit /b 1
