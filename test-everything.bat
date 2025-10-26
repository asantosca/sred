@echo off
REM Quick test script for BC Legal Tech
REM Tests all implemented features

echo ============================================================
echo BC Legal Tech - Quick Test Script
echo ============================================================
echo.

REM Check if Docker is running
echo Checking Docker services...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if services are up
echo Checking required services...
docker ps | findstr postgres >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] PostgreSQL not running. Starting services...
    docker-compose up -d
    timeout /t 5 /nobreak >nul
)

echo [OK] Services are running
echo.

REM Check if backend server is running
echo Checking backend server...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend server is not running at http://localhost:8000
    echo Please start it with: cd backend ^&^& uvicorn app.main:app --reload
    pause
    exit /b 1
)

echo [OK] Backend server is running
echo.

echo ============================================================
echo Running Tests...
echo ============================================================
echo.

REM Test 1: Register
echo Test 1: Register Company
curl -X POST http://localhost:8000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"company_name\":\"Test Firm\",\"admin_email\":\"test@example.com\",\"admin_password\":\"TestPass123\",\"admin_first_name\":\"Test\",\"admin_last_name\":\"User\"}" ^
  -s -o register_response.json -w "%%{http_code}"

set /p REGISTER_CODE=<register_response.json
if "%REGISTER_CODE:~0,1%"=="2" (
    echo [OK] Registration successful
) else (
    echo [FAIL] Registration failed
    type register_response.json
)
echo.

REM Test 2: Login
echo Test 2: Login
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123\"}" ^
  -s -o login_response.json -w "%%{http_code}"

if "%ERRORLEVEL%"=="0" (
    echo [OK] Login successful
) else (
    echo [FAIL] Login failed
)
echo.

REM Test 3: Email Service
echo Test 3: Email Service
cd backend
python test_email.py
cd ..
echo.

echo ============================================================
echo Test Summary
echo ============================================================
echo.
echo Next steps:
echo 1. Check MailHog at http://localhost:8025 to see test emails
echo 2. View full API docs at http://localhost:8000/docs
echo 3. Review detailed testing guide in docs/TESTING-GUIDE.md
echo.
echo ============================================================

pause
