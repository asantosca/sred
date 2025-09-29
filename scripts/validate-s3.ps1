# validate-s3.ps1 - S3/LocalStack validation for Windows

Write-Host "🔍 Validating LocalStack S3 setup..." -ForegroundColor Cyan

function Test-LocalStackHealth {
    try {
        Write-Host "1. Checking LocalStack health..." -ForegroundColor Yellow
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:4566/health" -UseBasicParsing -TimeoutSec 10
        $healthJson = $healthResponse.Content | ConvertFrom-Json
        
        if ($healthJson.features.s3 -eq "available") {
            Write-Host "   ✅ LocalStack S3 is healthy" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ❌ LocalStack S3 is not available" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "   ❌ LocalStack health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-S3Operations {
    Write-Host "`n2. Testing S3 operations..." -ForegroundColor Yellow
    
    $bucketName = "bc-legal-documents"
    $testFile = "test-validation-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $testContent = "BC Legal Tech - S3 Validation Test - $(Get-Date)"
    
    try {
        # List existing buckets
        Write-Host "   📋 Listing existing buckets..." -ForegroundColor Cyan
        $bucketsOutput = aws --endpoint-url=http://localhost:4566 s3 ls 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ S3 list buckets successful" -ForegroundColor Green
            if ($bucketsOutput) {
                Write-Host "      Existing buckets: $($bucketsOutput.Split("`n").Count) found" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ❌ S3 list buckets failed" -ForegroundColor Red
            return $false
        }
        
        # Create bucket if it doesn't exist
        Write-Host "   🪣 Creating/checking bucket: $bucketName..." -ForegroundColor Cyan
        aws --endpoint-url=http://localhost:4566 s3 mb "s3://$bucketName" 2>$null
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {  # 1 means bucket already exists
            Write-Host "   ✅ Bucket ready: $bucketName" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Bucket creation failed" -ForegroundColor Red
            return $false
        }
        
        # Upload test file
        Write-Host "   ⬆️  Uploading test file..." -ForegroundColor Cyan
        $testContent | aws --endpoint-url=http://localhost:4566 s3 cp - "s3://$bucketName/$testFile" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ File upload successful" -ForegroundColor Green
        } else {
            Write-Host "   ❌ File upload failed" -ForegroundColor Red
            return $false
        }
        
        # List objects in bucket
        Write-Host "   📋 Listing objects in bucket..." -ForegroundColor Cyan
        $objectsOutput = aws --endpoint-url=http://localhost:4566 s3 ls "s3://$bucketName/" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $objectCount = if ($objectsOutput) { ($objectsOutput.Split("`n") | Where-Object { $_.Trim() -ne "" }).Count } else { 0 }
            Write-Host "   ✅ Object listing successful ($objectCount objects found)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Object listing failed" -ForegroundColor Red
            return $false
        }
        
        # Download test file
        Write-Host "   ⬇️  Downloading test file..." -ForegroundColor Cyan
        $downloadedContent = aws --endpoint-url=http://localhost:4566 s3 cp "s3://$bucketName/$testFile" - 2>$null
        if ($LASTEXITCODE -eq 0 -and $downloadedContent -like "*BC Legal Tech*") {
            Write-Host "   ✅ File download successful" -ForegroundColor Green
        } else {
            Write-Host "   ❌ File download failed" -ForegroundColor Red
            return $false
        }
        
        # Generate presigned URL
        Write-Host "   🔗 Generating presigned URL..." -ForegroundColor Cyan
        $presignedUrl = aws --endpoint-url=http://localhost:4566 s3 presign "s3://$bucketName/$testFile" --expires-in 3600 2>$null
        if ($LASTEXITCODE -eq 0 -and $presignedUrl) {
            Write-Host "   ✅ Presigned URL generated successfully" -ForegroundColor Green
            Write-Host "      URL: $($presignedUrl.Substring(0, [Math]::Min(50, $presignedUrl.Length)))..." -ForegroundColor Gray
        } else {
            Write-Host "   ❌ Presigned URL generation failed" -ForegroundColor Red
        }
        
        # Test metadata operations
        Write-Host "   📝 Testing metadata operations..." -ForegroundColor Cyan
        aws --endpoint-url=http://localhost:4566 s3api put-object `
            --bucket $bucketName `
            --key "metadata-test.txt" `
            --body (New-TemporaryFile | ForEach-Object { "metadata test" | Out-File -FilePath $_.FullName -Encoding UTF8; $_.FullName }) `
            --metadata "company-id=test-company,document-type=legal-brief,confidentiality=high" `
            --content-type "text/plain" 2>$null
            
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Metadata operations successful" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Metadata operations failed" -ForegroundColor Red
        }
        
        # Cleanup test files
        Write-Host "   🗑️  Cleaning up test files..." -ForegroundColor Cyan
        aws --endpoint-url=http://localhost:4566 s3 rm "s3://$bucketName/$testFile" 2>$null
        aws --endpoint-url=http://localhost:4566 s3 rm "s3://$bucketName/metadata-test.txt" 2>$null
        
        return $true
    }
    catch {
        Write-Host "   ❌ S3 operations test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-PythonS3Integration {
    Write-Host "`n3. Testing Python S3 integration..." -ForegroundColor Yellow
    
    $pythonScript = @"
import boto3
import sys
try:
    s3 = boto3.client('s3', 
                      endpoint_url='http://localhost:4566',
                      aws_access_key_id='test', 
                      aws_secret_access_key='test',
                      region_name='us-west-2')
    
    buckets = s3.list_buckets()
    print(f'✅ Python S3 client working. Found {len(buckets["Buckets"])} buckets.')
    
    # Test basic operations
    bucket_name = 'bc-legal-documents'
    test_key = 'python-test.txt'
    test_content = b'Python S3 integration test'
    
    # Upload
    s3.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
    
    # Download
    response = s3.get_object(Bucket=bucket_name, Key=test_key)
    downloaded = response['Body'].read()
    
    # Cleanup
    s3.delete_object(Bucket=bucket_name, Key=test_key)
    
    if downloaded == test_content:
        print('✅ Python S3 upload/download cycle successful')
    else:
        print('❌ Python S3 content mismatch')
        
except Exception as e:
    print(f'❌ Python S3 client failed: {e}')
    sys.exit(1)
"@

    try {
        $pythonScript | python 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Python S3 integration working" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ❌ Python S3 integration failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "   ❌ Python S3 test error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-Summary {
    param($HealthOk, $OperationsOk, $PythonOk)
    
    Write-Host "`n📋 S3 Validation Summary:" -ForegroundColor Yellow
    Write-Host "   LocalStack Health: $(if($HealthOk){'✅ OK'}else{'❌ FAILED'})" -ForegroundColor $(if($HealthOk){'Green'}else{'Red'})
    Write-Host "   S3 Operations: $(if($OperationsOk){'✅ OK'}else{'❌ FAILED'})" -ForegroundColor $(if($OperationsOk){'Green'}else{'Red'})
    Write-Host "   Python Integration: $(if($PythonOk){'✅ OK'}else{'❌ FAILED'})" -ForegroundColor $(if($PythonOk){'Green'}else{'Red'})
    
    if ($HealthOk -and $OperationsOk -and $PythonOk) {
        Write-Host "`n🎉 All S3 tests passed! Your LocalStack setup is ready for BC Legal Tech development." -ForegroundColor Green
        
        Write-Host "`n🛠️ Quick reference commands:" -ForegroundColor Cyan
        Write-Host "   # List buckets" -ForegroundColor Gray
        Write-Host "   aws --endpoint-url=http://localhost:4566 s3 ls" -ForegroundColor White
        
        Write-Host "   # Create bucket" -ForegroundColor Gray
        Write-Host "   aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket" -ForegroundColor White
        
        Write-Host "   # Upload file" -ForegroundColor Gray
        Write-Host "   aws --endpoint-url=http://localhost:4566 s3 cp myfile.txt s3://my-bucket/" -ForegroundColor White
        
        Write-Host "   # List objects" -ForegroundColor Gray
        Write-Host "   aws --endpoint-url=http://localhost:4566 s3 ls s3://my-bucket/" -ForegroundColor White
        
        Write-Host "`n📝 Environment variables to use:" -ForegroundColor Cyan
        Write-Host "   AWS_ENDPOINT_URL=http://localhost:4566" -ForegroundColor White
        Write-Host "   AWS_ACCESS_KEY_ID=test" -ForegroundColor White
        Write-Host "   AWS_SECRET_ACCESS_KEY=test" -ForegroundColor White
        Write-Host "   S3_BUCKET_NAME=bc-legal-documents" -ForegroundColor White
        
    } else {
        Write-Host "`n❌ Some S3 tests failed. Check the errors above and:" -ForegroundColor Red
        Write-Host "   1. Ensure LocalStack container is running: docker-compose ps" -ForegroundColor Yellow
        Write-Host "   2. Check LocalStack logs: docker-compose logs localstack" -ForegroundColor Yellow
        Write-Host "   3. Restart LocalStack: docker-compose restart localstack-minimal" -ForegroundColor Yellow
        Write-Host "   4. Verify AWS CLI is installed and configured" -ForegroundColor Yellow
    }
}

# Main execution
Write-Host "Starting S3 validation for BC Legal Tech..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$healthOk = Test-LocalStackHealth
$operationsOk = if ($healthOk) { Test-S3Operations } else { $false }
$pythonOk = if ($operationsOk) { Test-PythonS3Integration } else { $false }

Show-Summary -HealthOk $healthOk -OperationsOk $operationsOk -PythonOk $pythonOk

Write-Host "`n✅ S3 validation complete!" -ForegroundColor Green