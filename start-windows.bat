@echo off
setlocal
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
  echo Please install and start Docker Desktop, then run this file again.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
docker compose up --build -d --wait
if errorlevel 1 (
  echo Startup failed. Read the error above, or run docker compose logs.
  pause
  exit /b 1
)
start "" http://localhost:8100
echo FLARE AI is running at http://localhost:8100
pause
