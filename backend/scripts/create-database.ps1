# create-database.ps1 - Create the SR&ED Intelligence database

Write-Host "Creating SR&ED Intelligence database..." -ForegroundColor Cyan

# Check if Docker services are running
Write-Host "`n1. Checking Docker services..." -ForegroundColor Yellow
$dockerStatus = docker-compose ps --quiet 2>$null
if (!$dockerStatus) {
    Write-Host "   WARNING: Docker services not running. Starting them..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
}
else {
    Write-Host "   SUCCESS: Docker services are running" -ForegroundColor Green
}

# Create the database
Write-Host "`n2. Creating database..." -ForegroundColor Yellow
try {
    # Connect to PostgreSQL and create database
    $createDbScript = @"
import asyncio
import asyncpg

async def create_database():
    try:
        # Connect to postgres database (default)
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
        
        # Check if database exists
        result = await conn.fetchval('SELECT 1 FROM pg_database WHERE datname = `$1', 'bc_legal_db')
        
        if result:
            print('INFO: Database bc_legal_db already exists')
        else:
            # Create the database
            await conn.execute('CREATE DATABASE bc_legal_db')
            print('SUCCESS: Database bc_legal_db created')
        
        await conn.close()
        
        # Now connect to the new database and enable extensions
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/bc_legal_db')
        
        # Enable UUID extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        print('SUCCESS: UUID extension enabled')
        
        # Try to enable pgvector extension
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            print('SUCCESS: pgvector extension enabled')
        except Exception as e:
            print(f'WARNING: pgvector extension not available: {e}')
        
        await conn.close()
        
    except Exception as e:
        print(f'ERROR: {e}')

asyncio.run(create_database())
"@

    python -c $createDbScript
    
}
catch {
    Write-Host "   ERROR: Failed to create database: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test connection to new database
Write-Host "`n3. Testing connection to bc_legal_db..." -ForegroundColor Yellow
try {
    python -c "
import asyncio
import asyncpg
async def test_connection():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/bc_legal_db')
        result = await conn.fetchval('SELECT version()')
        await conn.close()
        print('SUCCESS: Connected to bc_legal_db')
        print(f'PostgreSQL version: {result[:50]}...')
    except Exception as e:
        print(f'ERROR: {e}')
asyncio.run(test_connection())
"
    Write-Host "   SUCCESS: Database ready for migrations" -ForegroundColor Green
}
catch {
    Write-Host "   ERROR: Database connection test failed" -ForegroundColor Red
}

Write-Host "`nDatabase creation complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run setup-database.ps1 to create tables" -ForegroundColor White
Write-Host "2. Test your FastAPI server" -ForegroundColor White
