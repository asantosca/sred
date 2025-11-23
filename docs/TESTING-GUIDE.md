# BC Legal Tech - Testing Guide

## Testing Everything We've Built So Far

This guide shows you how to test all implemented features end-to-end.

---

## Prerequisites

### 1. Start All Services

```bash
# Start Docker services (PostgreSQL, Valkey, LocalStack, MailHog)
docker-compose up -d

# Wait a few seconds for services to start
docker ps
```

You should see:
- ✅ PostgreSQL (port 5432)
- ✅ Valkey (port 6379)
- ✅ LocalStack/S3 (port 4566)
- ✅ MailHog SMTP (port 1025) + Web UI (port 8025)

### 2. Set Up Database

```bash
cd backend

# Run migrations (creates all tables)
alembic upgrade head
```

### 3. Start Backend Server

**Option A: Direct Python**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Option B: Using venv**
```bash
cd backend
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload --port 8000
```

Server should start at: http://localhost:8000

### 4. Verify Server is Running

```bash
curl http://localhost:8000/health
```

Should return: `{"status": "healthy"}`

---

## Testing Method 1: Manual API Testing (curl)

### Step 1: Register a Company

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Law Firm",
    "admin_email": "admin@testfirm.com",
    "admin_password": "SecurePass123",
    "admin_first_name": "John",
    "admin_last_name": "Doe",
    "plan_tier": "professional"
  }'
```

**Expected Response**:
```json
{
  "user": {
    "id": "uuid...",
    "email": "admin@testfirm.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_admin": true,
    "company_id": "uuid...",
    "created_at": "2025-10-25T...",
    "last_active": null
  },
  "company": {
    "id": "uuid...",
    "name": "Test Law Firm",
    "plan_tier": "professional",
    "subscription_status": "trial",
    "created_at": "2025-10-25T..."
  },
  "token": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800,
    "refresh_token": "eyJ..."
  }
}
```

**Save these values**:
- `access_token`
- `refresh_token`
- `user.email`

### Step 2: Get Current User Info

```bash
# Replace YOUR_ACCESS_TOKEN with the token from Step 1
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected**: Same user/company info as registration

### Step 3: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@testfirm.com",
    "password": "SecurePass123"
  }'
```

**Expected**: New access_token and refresh_token

### Step 4: Test Refresh Token

```bash
# Replace YOUR_REFRESH_TOKEN with the token from login
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Expected**: New access_token and new refresh_token

**Test Token Rotation** (try to reuse old refresh token):
```bash
# Use the SAME refresh token again - should fail
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_OLD_REFRESH_TOKEN"
  }'
```

**Expected**: `401 Unauthorized - "Refresh token has been revoked"`

### Step 5: Test Password Reset Flow

**5a. Request Password Reset**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@testfirm.com"
  }'
```

**Expected**:
```json
{
  "message": "If the email exists, a password reset link has been sent",
  "detail": "Please check your email for instructions"
}
```

**5b. Check MailHog for Email**
- Open http://localhost:8025
- You should see a password reset email
- Click on it to view
- Find the reset token in the URL (after `token=`)
- Copy the token

**5c. Verify Reset Token**
```bash
# Replace YOUR_RESET_TOKEN with token from email
curl -X POST http://localhost:8000/api/v1/auth/password-reset/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN"
  }'
```

**Expected**:
```json
{
  "message": "Token is valid",
  "valid": true
}
```

**5d. Reset Password**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN",
    "new_password": "NewSecurePass456"
  }'
```

**Expected**: User info + new tokens (auto-login after reset)

**5e. Login with New Password**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@testfirm.com",
    "password": "NewSecurePass456"
  }'
```

**Expected**: Success with new tokens

**5f. Try to Reuse Reset Token** (should fail)
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN",
    "new_password": "AnotherPassword789"
  }'
```

**Expected**: `400 Bad Request - "Reset token has already been used"`

### Step 6: Test Email Service

```bash
cd backend
python test_email.py
```

**Expected Output**:
```
============================================================
BC Legal Tech - Email Service Test
============================================================

SMTP Configuration:
  Host: localhost
  Port: 1025
  From: noreply@bclegaltech.com

Test 1: Sending Password Reset Email...
  ✓ Password reset email sent successfully

Test 2: Sending User Invitation Email...
  ✓ User invitation email sent successfully

Test 3: Sending Welcome Email...
  ✓ Welcome email sent successfully

Test 4: Sending Custom Email...
  ✓ Custom email sent successfully

============================================================
Testing Complete!

View emails in MailHog:
  → http://localhost:8025
============================================================
```

Check MailHog at http://localhost:8025 - you should see 4 test emails.

---

## Testing Method 2: Postman Collection

### Import Collection

Create a Postman collection with these requests:

**Collection: BC Legal Tech**

1. **Register Company**
   - POST `{{base_url}}/api/v1/auth/register`
   - Body: JSON
   ```json
   {
     "company_name": "{{company_name}}",
     "admin_email": "{{admin_email}}",
     "admin_password": "{{admin_password}}",
     "admin_first_name": "John",
     "admin_last_name": "Doe"
   }
   ```
   - Tests (save tokens):
   ```javascript
   pm.environment.set("access_token", pm.response.json().token.access_token);
   pm.environment.set("refresh_token", pm.response.json().token.refresh_token);
   ```

2. **Login**
   - POST `{{base_url}}/api/v1/auth/login`
   - Body: JSON
   ```json
   {
     "email": "{{admin_email}}",
     "password": "{{admin_password}}"
   }
   ```

3. **Get Current User**
   - GET `{{base_url}}/api/v1/auth/me`
   - Headers: `Authorization: Bearer {{access_token}}`

4. **Refresh Token**
   - POST `{{base_url}}/api/v1/auth/refresh`
   - Body: JSON
   ```json
   {
     "refresh_token": "{{refresh_token}}"
   }
   ```

5. **Request Password Reset**
   - POST `{{base_url}}/api/v1/auth/password-reset/request`
   - Body: JSON
   ```json
   {
     "email": "{{admin_email}}"
   }
   ```

6. **Verify Reset Token**
   - POST `{{base_url}}/api/v1/auth/password-reset/verify`
   - Body: JSON
   ```json
   {
     "token": "{{reset_token}}"
   }
   ```

7. **Confirm Password Reset**
   - POST `{{base_url}}/api/v1/auth/password-reset/confirm`
   - Body: JSON
   ```json
   {
     "token": "{{reset_token}}",
     "new_password": "NewPassword123"
   }
   ```

**Environment Variables**:
```json
{
  "base_url": "http://localhost:8000",
  "company_name": "Test Law Firm",
  "admin_email": "admin@testfirm.com",
  "admin_password": "SecurePass123"
}
```

---

## Testing Method 3: Interactive API Docs (Swagger)

### 1. Open Swagger UI

Go to: http://localhost:8000/docs

### 2. Test Each Endpoint

**Register**:
1. Expand `POST /api/v1/auth/register`
2. Click "Try it out"
3. Fill in the example request
4. Click "Execute"
5. Copy `access_token` from response

**Get Current User**:
1. Click 🔓 "Authorize" button at top
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click "Authorize"
4. Now all endpoints will use this token
5. Try `GET /api/v1/auth/me`

**Continue testing all endpoints...**

---

## Testing Method 4: Python Test Script

Create `backend/test_complete_flow.py`:

```python
#!/usr/bin/env python3
"""
Complete end-to-end test of all implemented features
"""

import asyncio
import httpx
import sys
from rich.console import Console
from rich.table import Table

console = Console()

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "TestPassword123"
NEW_PASSWORD = "NewPassword456"

async def test_complete_flow():
    """Test the complete authentication flow"""

    async with httpx.AsyncClient() as client:
        console.print("\n[bold cyan]Starting Complete Flow Test[/bold cyan]\n")

        # Test 1: Register
        console.print("[yellow]Test 1: Register Company[/yellow]")
        register_response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "company_name": "Test Law Firm",
                "admin_email": TEST_EMAIL,
                "admin_password": TEST_PASSWORD,
                "admin_first_name": "Test",
                "admin_last_name": "User"
            }
        )

        if register_response.status_code == 201:
            console.print("  ✓ Registration successful", style="green")
            data = register_response.json()
            access_token = data["token"]["access_token"]
            refresh_token = data["token"]["refresh_token"]
        else:
            console.print(f"  ✗ Registration failed: {register_response.text}", style="red")
            return

        # Test 2: Get current user
        console.print("\n[yellow]Test 2: Get Current User[/yellow]")
        me_response = await client.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if me_response.status_code == 200:
            console.print("  ✓ Got user info", style="green")
        else:
            console.print(f"  ✗ Failed: {me_response.text}", style="red")

        # Test 3: Login
        console.print("\n[yellow]Test 3: Login[/yellow]")
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        if login_response.status_code == 200:
            console.print("  ✓ Login successful", style="green")
            new_tokens = login_response.json()["token"]
        else:
            console.print(f"  ✗ Login failed: {login_response.text}", style="red")

        # Test 4: Refresh token
        console.print("\n[yellow]Test 4: Refresh Token[/yellow]")
        refresh_response = await client.post(
            f"{BASE_URL}/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        if refresh_response.status_code == 200:
            console.print("  ✓ Token refreshed", style="green")
            access_token = refresh_response.json()["access_token"]
            new_refresh_token = refresh_response.json()["refresh_token"]
        else:
            console.print(f"  ✗ Refresh failed: {refresh_response.text}", style="red")

        # Test 5: Request password reset
        console.print("\n[yellow]Test 5: Request Password Reset[/yellow]")
        reset_request_response = await client.post(
            f"{BASE_URL}/api/v1/auth/password-reset/request",
            json={"email": TEST_EMAIL}
        )

        if reset_request_response.status_code == 200:
            console.print("  ✓ Reset email sent (check MailHog at http://localhost:8025)", style="green")
            console.print("  [dim]Note: You'll need to manually get the token from MailHog[/dim]")
        else:
            console.print(f"  ✗ Reset request failed: {reset_request_response.text}", style="red")

        # Summary
        console.print("\n[bold green]✓ All automated tests passed![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Check MailHog at http://localhost:8025")
        console.print("2. View the password reset email")
        console.print("3. Copy the reset token")
        console.print("4. Test the reset flow manually")

if __name__ == "__main__":
    try:
        asyncio.run(test_complete_flow())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
```

Run it:
```bash
cd backend
pip install rich  # For pretty output
python test_complete_flow.py
```

---

## Verification Checklist

Use this checklist to ensure everything works:

### Authentication Features

- [ ] **Company Registration**
  - [ ] Create new company with admin user
  - [ ] Returns access + refresh tokens
  - [ ] Email validation works
  - [ ] Password validation works (8+ chars, uppercase, lowercase, digit)

- [ ] **Login**
  - [ ] Login with correct credentials
  - [ ] Returns access + refresh tokens
  - [ ] Reject invalid credentials
  - [ ] Reject inactive users

- [ ] **JWT Middleware**
  - [ ] `/auth/me` requires valid token
  - [ ] Returns 401 with invalid token
  - [ ] Returns 401 with expired token
  - [ ] Returns user + company info when valid

- [ ] **Refresh Tokens**
  - [ ] Can refresh access token with valid refresh token
  - [ ] Returns new access + refresh tokens
  - [ ] Old refresh token is revoked (can't reuse)
  - [ ] Invalid refresh token returns 401

### Password Reset

- [ ] **Request Reset**
  - [ ] Always returns success (even for non-existent email)
  - [ ] Email sent to valid addresses
  - [ ] Email contains reset link
  - [ ] Old tokens invalidated

- [ ] **Verify Token**
  - [ ] Valid token returns success
  - [ ] Invalid token returns 400
  - [ ] Expired token returns 400
  - [ ] Used token returns 400

- [ ] **Confirm Reset**
  - [ ] Can reset password with valid token
  - [ ] Returns new tokens (auto-login)
  - [ ] Can login with new password
  - [ ] Token marked as used (can't reuse)
  - [ ] Password validation enforced

### Email Service

- [ ] **MailHog Integration**
  - [ ] MailHog running on port 8025
  - [ ] Emails appear in MailHog UI
  - [ ] HTML emails render correctly
  - [ ] Plain text fallback present

- [ ] **Email Templates**
  - [ ] Password reset email
  - [ ] User invitation email
  - [ ] Welcome email
  - [ ] Custom emails

### Database

- [ ] **Migrations**
  - [ ] All tables created
  - [ ] Refresh tokens table exists
  - [ ] Password reset tokens table exists
  - [ ] Indexes created

- [ ] **Data Integrity**
  - [ ] Foreign keys enforced
  - [ ] Unique constraints work
  - [ ] Timestamps auto-populated

---

## Common Issues & Solutions

### Issue: Cannot connect to database

**Solution**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart if needed
docker-compose restart postgres

# Check logs
docker logs bc-legal-postgres
```

### Issue: MailHog not receiving emails

**Solution**:
```bash
# Check if MailHog is running
docker ps | grep mailhog

# Restart if needed
docker-compose restart mailhog

# Verify connection
telnet localhost 1025
```

### Issue: 401 Unauthorized on /auth/me

**Solution**:
- Check token format: Must be `Bearer YOUR_TOKEN`
- Verify token hasn't expired (30 min lifetime)
- Check JWT_SECRET_KEY matches between token creation and validation

### Issue: Refresh token already revoked

**Expected Behavior**: This is security feature - refresh tokens can only be used once

**Solution**: Get a new refresh token by:
1. Logging in again, OR
2. Using the most recent refresh token from last refresh

### Issue: Password reset token invalid

**Possible Causes**:
- Token expired (1 hour lifetime)
- Token already used
- Token doesn't exist

**Solution**: Request a new password reset

---

## Performance Testing

### Test Token Performance

```bash
# Generate 100 users and test login speed
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{
      \"company_name\": \"Firm $i\",
      \"admin_email\": \"user$i@test.com\",
      \"admin_password\": \"Password123\"
    }" &
done
wait
```

---

## Clean Up After Testing

### Reset Database

```bash
cd backend

# Drop all tables
alembic downgrade base

# Recreate tables
alembic upgrade head
```

### Clear MailHog Emails

```bash
# Delete all emails in MailHog
curl -X DELETE http://localhost:8025/api/v1/messages
```

### Stop Services

```bash
docker-compose down
```

---

## Next Steps

Once all tests pass:

1. ✅ All authentication features working
2. ✅ Ready to build user profile endpoints
3. ✅ Ready to build document management
4. ✅ Ready to start frontend integration

---

## Quick Test Command

For a quick smoke test:

```bash
# One-liner to test registration + login
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Quick Test","admin_email":"quick@test.com","admin_password":"Password123"}' \
  && curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"quick@test.com","password":"Password123"}'
```

If both return 200/201 with tokens, basic auth is working! ✅
