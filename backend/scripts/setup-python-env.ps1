# setup-python-env.ps1 - Python virtual environment setup for SR&ED Intelligence

python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# 4. Activate virtual environment
Write-Host "`n4. Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "   SUCCESS: Virtual environment activated" -ForegroundColor Green
}
catch {
    Write-Host "   WARNING: PowerShell execution policy issue. Running fix..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "   SUCCESS: Virtual environment activated after policy fix" -ForegroundColor Green
}

# 5. Upgrade pip
Write-Host "`n5. Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "   SUCCESS: Pip upgraded" -ForegroundColor Green

# 6. Install FastAPI dependencies
Write-Host "`n6. Installing FastAPI dependencies..." -ForegroundColor Yellow
$dependencies = @(
    "fastapi[all]==0.104.1",
    "uvicorn[standard]==0.24.0",
    "sqlalchemy==2.0.23",
    "alembic==1.12.1",
    "psycopg2-binary==2.9.7",
    "redis==5.0.1",
    "boto3==1.29.7",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.6",
    "pydantic-settings==2.0.3",
    "pgvector==0.2.4",
    "openai==1.3.5",
    "python-dotenv==1.0.0"
)

foreach ($package in $dependencies) {
    Write-Host "   Installing $package..." -ForegroundColor Gray
    pip install $package
}
Write-Host "   SUCCESS: All dependencies installed" -ForegroundColor Green

# 7. Create requirements.txt
Write-Host "`n7. Creating requirements.txt..." -ForegroundColor Yellow
pip freeze > requirements.txt
Write-Host "   SUCCESS: requirements.txt created" -ForegroundColor Green

# 8. Create .env file template
Write-Host "`n8. Creating environment configuration..." -ForegroundColor Yellow
$envContent = @"
# SR&ED Intelligence - Environment Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bc_legal_db
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566
S3_BUCKET_NAME=bc-legal-documents
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
DEBUG=true
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "   SUCCESS: .env file created" -ForegroundColor Green

Write-Host "`nPython environment setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Stay in backend directory" -ForegroundColor White
Write-Host "2. Virtual environment is already activated" -ForegroundColor White
Write-Host "3. Ready to create FastAPI project structure" -ForegroundColor White
Write-Host "`nTo reactivate venv later: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow