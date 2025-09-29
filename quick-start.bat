@echo off
REM quick-start.bat - Quick commands for BC Legal Tech development on Windows

echo 🚀 BC Legal Tech - Quick Start Commands
echo =====================================

if "%1"=="validate" goto validate
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="logs" goto logs
if "%1"=="reset" goto reset
if "%1"=="s3" goto s3test
if "%1"=="backend" goto backend
if "%1"=="frontend" goto frontend
if "%1"=="setup" goto setup

echo Usage: quick-start.bat [command]
echo.
echo Available commands:
echo   setup     - Full environment setup
echo   validate  - Validate all services
echo   start     - Start all Docker services
echo   stop      - Stop all Docker services
echo   logs      - Show service logs
echo   reset     - Reset all data (destructive!)
echo   s3        - Test S3/LocalStack
echo   backend   - Start backend server
echo   frontend  - Start frontend server
echo.
echo Examples:
echo   quick-start.bat setup
echo   quick-start.bat validate
echo   quick-start.bat start
goto end

:setup
echo 🔧 Running full environment setup...
powershell -ExecutionPolicy Bypass -File "setup-environment.ps1"
goto end

:validate
echo 🔍 Validating BC Legal Tech services...
powershell -ExecutionPolicy Bypass -File "validate-setup.ps1"
goto end

:start
echo 🐳 Starting Docker services...
docker-compose up -d
echo ✅ Services started. Run 'quick-start validate' to check status.
goto end

:stop
echo 🛑 Stopping Docker services...
docker-compose down
echo ✅ Services stopped.
goto end

:logs
if "%2"=="" (
    echo 📋 Showing logs for all services...
    docker-compose logs --tail=50 -f
) else (
    echo 📋 Showing logs for %2...
    docker-compose logs --tail=50 -f %2
)
goto end

:reset
echo ⚠️  WARNING: This will delete all data!
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    echo 🗑️  Resetting all data...
    docker-compose down -v
    docker system prune -f
    echo ✅ Data reset complete.
) else (
    echo ❌ Reset cancelled.
)
goto end

:s3test
echo 📦 Testing S3/LocalStack...
powershell -ExecutionPolicy Bypass -File "validate-s3.ps1"
goto end

:backend
echo 🐍 Starting backend server...
cd backend
echo Starting FastAPI server at http://localhost:8000
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd ..
goto end

:frontend
echo ⚛️  Starting frontend server...
cd frontend
echo Starting React development server at http://localhost:5173
npm run dev
cd ..
goto end

:end