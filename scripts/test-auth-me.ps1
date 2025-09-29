# test-auth-me.ps1 - Login and test /me endpoint

Write-Host "Testing BC Legal Tech authentication..." -ForegroundColor Cyan

$baseUrl = "http://127.0.0.1:8000/api/v1"

# Step 1: Login
Write-Host "`n1. Logging in..." -ForegroundColor Yellow

$loginBody = @{
    email    = "user@examplePostman.com"
    password = "ThisPassword123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json"
    
    $loginData = $loginResponse.Content | ConvertFrom-Json
    $token = $loginData.token.access_token
    
    Write-Host "   SUCCESS: Logged in as $($loginData.user.email)" -ForegroundColor Green
    Write-Host "   Token: $($token.Substring(0, 50))..." -ForegroundColor Gray
    
}
catch {
    Write-Host "   ERROR: Login failed - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Call /me endpoint
Write-Host "`n2. Calling /me endpoint..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $token"
}

try {
    $meResponse = Invoke-WebRequest -Uri "$baseUrl/auth/me" `
        -Method GET `
        -Headers $headers
    
    $meData = $meResponse.Content | ConvertFrom-Json
    
    Write-Host "   SUCCESS: Retrieved current user information" -ForegroundColor Green
    Write-Host "`n--- User Information ---" -ForegroundColor Cyan
    Write-Host "Email: $($meData.user.email)"
    Write-Host "Name: $($meData.user.first_name) $($meData.user.last_name)"
    Write-Host "Admin: $($meData.user.is_admin)"
    Write-Host "Active: $($meData.user.is_active)"
    
    Write-Host "`n--- Company Information ---" -ForegroundColor Cyan
    Write-Host "Company: $($meData.company.name)"
    Write-Host "Plan: $($meData.company.plan_tier)"
    Write-Host "Status: $($meData.company.subscription_status)"
    
    Write-Host "`n--- Full Response ---" -ForegroundColor Cyan
    $meData | ConvertTo-Json -Depth 10
    
}
catch {
    Write-Host "   ERROR: Failed to get current user - $($_.Exception.Message)" -ForegroundColor Red
    
    # Show detailed error if available
    if ($_.ErrorDetails.Message) {
        Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`nTest complete!" -ForegroundColor Green
