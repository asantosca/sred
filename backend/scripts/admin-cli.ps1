# BC Legal Tech - Admin CLI
# Interactive script for testing admin endpoints

param(
    [string]$BaseUrl = "http://localhost:8000"
)

$global:AdminToken = $null

function Write-Header {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  BC Legal Tech - Admin CLI" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Get-Credentials {
    Write-Host "Enter your admin credentials:" -ForegroundColor Yellow
    $email = Read-Host "Email"
    $password = Read-Host "Password" -AsSecureString
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    )
    return @{
        email = $email
        password = $plainPassword
    }
}

function Get-Token {
    param([hashtable]$Credentials)

    $body = @{
        email = $Credentials.email
        password = $Credentials.password
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body

        # Token is nested under response.token.access_token
        if ($response.token.access_token) {
            $global:AdminToken = $response.token.access_token
        } elseif ($response.access_token) {
            $global:AdminToken = $response.access_token
        } else {
            Write-Host "`nUnexpected response format:" -ForegroundColor Yellow
            Write-Host ($response | ConvertTo-Json -Depth 3)
            return $false
        }

        if ($global:AdminToken) {
            Write-Host "`nAuthentication successful!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "`nNo token in response" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "`nAuthentication failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host $_.ErrorDetails.Message -ForegroundColor Red
        }
        return $false
    }
}

function Invoke-AdminApi {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$QueryParams = @{}
    )

    if (-not $global:AdminToken) {
        Write-Host "Not authenticated. Please login first." -ForegroundColor Red
        return $null
    }

    $uri = "$BaseUrl$Endpoint"
    if ($QueryParams.Count -gt 0) {
        $queryString = ($QueryParams.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
        $uri = "$uri`?$queryString"
    }

    $headers = @{
        "Authorization" = "Bearer " + $global:AdminToken
    }

    try {
        $response = Invoke-RestMethod -Uri $uri `
            -Method $Method `
            -Headers $headers
        return $response
    }
    catch {
        Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host $_.ErrorDetails.Message -ForegroundColor Red
        }
        return $null
    }
}

function Show-JsonResponse {
    param($Response)
    if ($Response) {
        $Response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor White
    }
}

# Menu Commands
function Get-UsageSummary {
    Write-Host "`n--- Usage Summary ---" -ForegroundColor Cyan
    $days = Read-Host "Days to look back (default: 30)"
    if ([string]::IsNullOrEmpty($days)) { $days = "30" }

    $params = @{ days = $days }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/usage" -QueryParams $params
    Show-JsonResponse $response
}

function Get-UsageByCompany {
    Write-Host "`n--- Usage by Company ---" -ForegroundColor Cyan
    $companyId = Read-Host "Company ID (UUID)"
    $days = Read-Host "Days to look back (default: 30)"
    if ([string]::IsNullOrEmpty($days)) { $days = "30" }

    $params = @{ days = $days; company_id = $companyId }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/usage" -QueryParams $params
    Show-JsonResponse $response
}

function Get-DailyUsage {
    Write-Host "`n--- Daily Usage ---" -ForegroundColor Cyan
    $days = Read-Host "Days to look back (default: 30)"
    if ([string]::IsNullOrEmpty($days)) { $days = "30" }

    $params = @{ days = $days }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/usage/daily" -QueryParams $params
    Show-JsonResponse $response
}

function Get-DailyUsageByService {
    Write-Host "`n--- Daily Usage by Service ---" -ForegroundColor Cyan
    Write-Host "Services: claude_chat, claude_summary, openai_embeddings, textract_ocr"
    $service = Read-Host "Service name"
    $days = Read-Host "Days to look back (default: 30)"
    if ([string]::IsNullOrEmpty($days)) { $days = "30" }

    $params = @{ days = $days; service = $service }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/usage/daily" -QueryParams $params
    Show-JsonResponse $response
}

function Get-Companies {
    Write-Host "`n--- All Companies ---" -ForegroundColor Cyan
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/companies"
    Show-JsonResponse $response
}

function Get-FeedbackStats {
    Write-Host "`n--- Feedback Statistics ---" -ForegroundColor Cyan
    $days = Read-Host "Days to look back (default: 30)"
    if ([string]::IsNullOrEmpty($days)) { $days = "30" }

    $params = @{ days = $days }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/feedback/stats" -QueryParams $params
    Show-JsonResponse $response
}

function Get-FeedbackStatsByCompany {
    Write-Host "`n--- Feedback Stats by Company ---" -ForegroundColor Cyan
    $companyId = Read-Host "Company ID (UUID)"
    $days = Read-Host "Days to look back (default: 7)"
    if ([string]::IsNullOrEmpty($days)) { $days = "7" }

    $params = @{ days = $days; company_id = $companyId }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/feedback/stats" -QueryParams $params
    Show-JsonResponse $response
}

function Get-QualityAlerts {
    Write-Host "`n--- Active Quality Alerts ---" -ForegroundColor Cyan
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/feedback/alerts"
    Show-JsonResponse $response
}

function Get-FlaggedMessages {
    Write-Host "`n--- Flagged Messages ---" -ForegroundColor Cyan
    $limit = Read-Host "Limit (default: 50)"
    if ([string]::IsNullOrEmpty($limit)) { $limit = "50" }

    $params = @{ limit = $limit }
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/feedback/flagged" -QueryParams $params
    Show-JsonResponse $response
}

function Invoke-CheckAlerts {
    Write-Host "`n--- Trigger Alert Check ---" -ForegroundColor Cyan
    $response = Invoke-AdminApi -Endpoint "/api/v1/admin/feedback/check-alerts" -Method "POST"
    Show-JsonResponse $response
}

function Show-Menu {
    Write-Host ""
    Write-Host "COST REPORTING" -ForegroundColor Yellow
    Write-Host "  1. Get usage summary"
    Write-Host "  2. Get usage by company"
    Write-Host "  3. Get daily usage"
    Write-Host "  4. Get daily usage by service"
    Write-Host "  5. List all companies"
    Write-Host ""
    Write-Host "FEEDBACK ANALYTICS" -ForegroundColor Yellow
    Write-Host "  6. Get feedback statistics"
    Write-Host "  7. Get feedback stats by company"
    Write-Host "  8. Get active quality alerts"
    Write-Host "  9. Get flagged messages"
    Write-Host " 10. Trigger alert check"
    Write-Host ""
    Write-Host "OTHER" -ForegroundColor Yellow
    Write-Host "  R. Re-authenticate"
    Write-Host "  Q. Quit"
    Write-Host ""
}

# Main
Write-Header

$creds = Get-Credentials
$authenticated = Get-Token -Credentials $creds

if (-not $authenticated) {
    Write-Host "Failed to authenticate. Exiting." -ForegroundColor Red
    exit 1
}

while ($true) {
    Show-Menu
    $choice = Read-Host "Select option"

    switch ($choice.ToUpper()) {
        "1" { Get-UsageSummary }
        "2" { Get-UsageByCompany }
        "3" { Get-DailyUsage }
        "4" { Get-DailyUsageByService }
        "5" { Get-Companies }
        "6" { Get-FeedbackStats }
        "7" { Get-FeedbackStatsByCompany }
        "8" { Get-QualityAlerts }
        "9" { Get-FlaggedMessages }
        "10" { Invoke-CheckAlerts }
        "R" {
            $creds = Get-Credentials
            Get-Token -Credentials $creds
        }
        "Q" {
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "Invalid option. Please try again." -ForegroundColor Red
        }
    }

    Write-Host "`nPress Enter to continue..." -ForegroundColor Gray
    Read-Host
}
