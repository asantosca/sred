# setup-python312.ps1 - Clean setup of Python 3.12 LTS

Write-Host "Setting up Python 3.12 LTS for BC Legal Tech" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

function Remove-OldPython {
    Write-Host "`nStep 1: Removing old Python versions..." -ForegroundColor Yellow
    
    # Remove Python 3.9
    try {
        Write-Host "  Removing Python 3.9..." -ForegroundColor Cyan
        winget uninstall Python.Python.3.9 --silent 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] Python 3.9 removed" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Python 3.9 not found or already removed" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  [INFO] Python 3.9 removal skipped" -ForegroundColor Gray
    }
    
    # Remove Python 3.13 if it exists
    try {
        Write-Host "  Checking for Python 3.13..." -ForegroundColor Cyan
        winget uninstall Python.Python.3.13 --silent 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] Python 3.13 removed" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Python 3.13 not found" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  [INFO] Python 3.13 removal skipped" -ForegroundColor Gray
    }
}

function Install-Python312 {
    Write-Host "`nStep 2: Installing Python 3.12 LTS..." -ForegroundColor Yellow
    
    try {
        Write-Host "  Installing Python 3.12 via winget..." -ForegroundColor Cyan
        winget install Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] Python 3.12 LTS installed" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  [ERROR] Winget installation failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  [ERROR] Installation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Verify-Python312 {
    Write-Host "`nStep 3: Verifying Python 3.12 installation..." -ForegroundColor Yellow
    
    # Refresh PATH
    Write-Host "  Refreshing environment..." -ForegroundColor Cyan
    $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [Environment]::GetEnvironmentVariable("PATH", "Machine")
    
    # Test python command
    try {
        $version = python --version 2>$null
        if ($version -like "*3.12*") {
            Write-Host "  [SUCCESS] python --version: $version" -ForegroundColor Green
            
            # Test basic functionality
            $testResult = python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} ready')" 2>$null
            Write-Host "  [SUCCESS] Python test: $testResult" -ForegroundColor Green
            
            return $true
        } else {
            Write-Host "  [ERROR] Wrong Python version: $version" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  [ERROR] Python not accessible: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Update-PyprojectToml {
    Write-Host "`nStep 4: Updating pyproject.toml..." -ForegroundColor Yellow
    
    $pyprojectPath = "bc-legal-backend\pyproject.toml"
    
    if (Test-Path $pyprojectPath) {
        try {
            # Read current content
            $content = Get-Content $pyprojectPath -Raw
            
            # Update Python version requirement
            $updatedContent = $content -replace 'python = "\^3\.\d+"', 'python = "^3.12"'
            
            # Write back to file
            Set-Content -Path $pyprojectPath -Value $updatedContent -Encoding UTF8
            
            Write-Host "  [SUCCESS] Updated pyproject.toml to use Python ^3.12" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "  [ERROR] Failed to update pyproject.toml: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "  [WARNING] pyproject.toml not found at $pyprojectPath" -ForegroundColor Yellow
        return $false
    }
}

function Configure-Poetry {
    Write-Host "`nStep 5: Configuring Poetry..." -ForegroundColor Yellow
    
    try {
        # Check Poetry installation
        $poetryVersion = poetry --version 2>$null
        Write-Host "  Found Poetry: $poetryVersion" -ForegroundColor Gray
        
        # Remove any existing virtual environments
        Write-Host "  Cleaning old Poetry environments..." -ForegroundColor Cyan
        Set-Location "bc-legal-backend" -ErrorAction SilentlyContinue
        poetry env remove --all 2>$null
        
        # Configure Poetry to use Python 3.12
        Write-Host "  Configuring Poetry for Python 3.12..." -ForegroundColor Cyan
        poetry env use python
        
        # Show environment info
        $envInfo = poetry env info --path 2>$null
        Write-Host "  [SUCCESS] Poetry environment: $envInfo" -ForegroundColor Green
        
        Set-Location ".." -ErrorAction SilentlyContinue
        return $true
    }
    catch {
        Write-Host "  [ERROR] Poetry configuration failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-Installation {
    Write-Host "`nStep 6: Testing complete setup..." -ForegroundColor Yellow
    
    Set-Location "bc-legal-backend" -ErrorAction SilentlyContinue
    
    try {
        # Test Poetry install
        Write-Host "  Testing poetry install..." -ForegroundColor Cyan
        poetry install --dry-run 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] Poetry dependency resolution working" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] Poetry dependency issues detected" -ForegroundColor Yellow
        }
        
        # Test Poetry Python version
        $poetryPython = poetry run python --version 2>$null
        if ($poetryPython -like "*3.12*") {
            Write-Host "  [SUCCESS] Poetry using Python 3.12: $poetryPython" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Poetry using wrong Python: $poetryPython" -ForegroundColor Red
        }
        
        Set-Location ".." -ErrorAction SilentlyContinue
        return $true
    }
    catch {
        Write-Host "  [ERROR] Installation test failed: $($_.Exception.Message)" -ForegroundColor Red
        Set-Location ".." -ErrorAction SilentlyContinue
        return $false
    }
}

function Show-NextSteps {
    Write-Host "`n[SUCCESS] Python 3.12 LTS setup complete!" -ForegroundColor Green
    
    Write-Host "`nSetup Summary:" -ForegroundColor Cyan
    Write-Host "  - Python 3.12 LTS installed (supported until 2028)" -ForegroundColor White
    Write-Host "  - pyproject.toml updated for Python ^3.12" -ForegroundColor White
    Write-Host "  - Poetry configured for Python 3.12" -ForegroundColor White
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "1. Install backend dependencies:" -ForegroundColor White
    Write-Host "   cd bc-legal-backend" -ForegroundColor Gray
    Write-Host "   poetry install" -ForegroundColor Gray
    
    Write-Host "2. Start FastAPI development server:" -ForegroundColor White
    Write-Host "   poetry run uvicorn app.main:app --reload" -ForegroundColor Gray
    
    Write-Host "3. View API documentation:" -ForegroundColor White
    Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray
    
    Write-Host "`nVerification Commands:" -ForegroundColor Yellow
    Write-Host "   python --version              # Should show Python 3.12.x" -ForegroundColor Gray
    Write-Host "   poetry env info               # Should show Python 3.12 path" -ForegroundColor Gray
    Write-Host "   poetry run python --version   # Should show Python 3.12.x" -ForegroundColor Gray
    
    Write-Host "`nReady to build BC Legal Tech backend!" -ForegroundColor Green
}

# Main execution
try {
    Write-Host "Starting Python 3.12 LTS setup..." -ForegroundColor White
    
    Remove-OldPython
    
    $installSuccess = Install-Python312
    if (-not $installSuccess) {
        Write-Host "`n[ERROR] Python 3.12 installation failed. Try manual installation:" -ForegroundColor Red
        Write-Host "https://www.python.org/downloads/release/python-3129/" -ForegroundColor Gray
        exit 1
    }
    
    Start-Sleep -Seconds 5  # Give installation time to register
    
    $verifySuccess = Verify-Python312
    if (-not $verifySuccess) {
        Write-Host "`n[ERROR] Python 3.12 verification failed. Please restart terminal and try again." -ForegroundColor Red
        exit 1
    }
    
    Update-PyprojectToml
    Configure-Poetry
    Test-Installation
    
    Show-NextSteps
    
} catch {
    Write-Host "`n[ERROR] Setup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please try manual installation or restart terminal and run again." -ForegroundColor Yellow
}