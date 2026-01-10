# scripts/reset_db.ps1 - Reset Database Schema and Apply RLS

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Resolve-Path "$ScriptRoot\.."

# Switch to project root to ensure docker-compose finds the configuration
Push-Location $ProjectRoot

try {
    Write-Host "1. Ensuring PostgreSQL is running..."
    docker-compose up -d postgres

    Write-Host "2. Dropping existing schema 'bc_legal_ds' and migration history..."
    docker-compose exec -T postgres psql -U postgres -d bc_legal_db -c "DROP SCHEMA IF EXISTS bc_legal_ds CASCADE; DROP TABLE IF EXISTS public.alembic_version;"

    Write-Host "3. Running Alembic Migrations (High-Speed Container)..."
    docker-compose run --rm celery-worker alembic upgrade head

    Write-Host "4. Applying Row-Level Security (RLS) Policies and Triggers..."
    $rlsFile = Join-Path $ProjectRoot "apply-rls.sql"
    
    if (-not (Test-Path $rlsFile)) {
        Write-Error "Error: Could not find apply-rls.sql at '$rlsFile'"
        exit 1
    }

    Get-Content $rlsFile | docker-compose exec -T postgres psql -U postgres -d bc_legal_db

    Write-Host "✅ Database reset complete! You can now start the backend."
}
finally {
    # Return to original directory
    Pop-Location
}
