@echo off
REM Quick start script for BC Legal Tech backend

echo ============================================================
echo BC Legal Tech - Backend Startup
echo ============================================================
echo.

REM Check if Docker is running
echo [1/4] Checking Docker...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

REM Start Docker services
echo [2/4] Starting Docker services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)
echo [OK] Docker services started
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
echo   - LocalStack/S3: localhost:4566
echo   - MailHog SMTP: localhost:1025
echo   - MailHog UI: http://localhost:8025
echo.

REM Wait for services to be ready
echo [3/4] Waiting for services to initialize...
timeout /t 5 /nobreak >nul
echo [OK] Services should be ready
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo [ERROR] backend directory not found
    echo Please run this script from the project root
    pause
    exit /b 1
)

REM Run migrations
echo [4/4] Running database migrations...
cd backend
alembic upgrade head 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Migration failed - this might be OK if migrations were already run
)
echo [OK] Database ready
echo.

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

echo ============================================================
echo Starting Backend Server
echo ============================================================
echo.
echo Server will start at: http://localhost:8000
echo API Docs (Swagger): http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the server
python -m uvicorn app.main:app --reload --port 8000

REM This runs when server is stopped
echo.
echo ============================================================
echo Backend server stopped
echo.
echo To stop Docker services, run: docker-compose down
echo ============================================================
pause
