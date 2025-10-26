# Password Reset Flow Implementation

## Overview

This document describes the complete password reset implementation for BC Legal Tech, including security measures and best practices.

## What Was Implemented

### 1. Database Model
**File**: [backend/app/models/models.py:93-106](../backend/app/models/models.py#L93-L106)

Created `PasswordResetToken` model with:
- `id`: Unique identifier (UUID)
- `user_id`: Foreign key to users table
- `token_hash`: SHA-256 hash of the reset token (secure storage)
- `expires_at`: Expiration timestamp (1 hour by default)
- `is_used`: Boolean flag to prevent token reuse
- `created_at`: Token creation timestamp
- `used_at`: Token usage timestamp (nullable)

**Security Features**:
- Tokens stored as SHA-256 hashes, never plaintext
- Indexed on `token_hash` for fast lookups
- One-time use only (marked as used after password reset)
- Short expiration (1 hour)

### 2. Schemas
**File**: [backend/app/schemas/auth.py:87-110](../backend/app/schemas/auth.py#L87-L110)

Created schemas:
- `PasswordResetRequest`: Request reset with email
- `PasswordResetVerify`: Verify token validity
- `PasswordResetConfirm`: Complete reset with new password

**Validation**:
- Email validation
- Strong password requirements (8+ chars, uppercase, lowercase, digit)

### 3. AuthService Methods
**File**: [backend/app/services/auth.py:339-480](../backend/app/services/auth.py#L339-L480)

Added methods:
- `request_password_reset(email)`: Create reset token and invalidate old ones
- `verify_password_reset_token(token)`: Validate token without consuming it
- `reset_password(token, new_password)`: Complete the password reset

**Security Features**:
- Prevents email enumeration (always returns success)
- Invalidates old tokens when new one is requested
- One-time use tokens
- Comprehensive validation

### 4. API Endpoints
**File**: [backend/app/api/v1/endpoints/auth.py:180-275](../backend/app/api/v1/endpoints/auth.py#L180-L275)

Created endpoints:
- `POST /api/v1/auth/password-reset/request`: Request password reset
- `POST /api/v1/auth/password-reset/verify`: Verify token
- `POST /api/v1/auth/password-reset/confirm`: Reset password

### 5. Email Integration
Uses the email service to send password reset emails with:
- Professional HTML template
- Reset link with token
- 1-hour expiration notice
- Plain text fallback

### 6. Database Migration
**File**: [backend/alembic/versions/002_add_password_reset_tokens_table.py](../backend/alembic/versions/002_add_password_reset_tokens_table.py)

Created migration for `password_reset_tokens` table.

## Password Reset Flow

### Complete User Journey

```
1. User Forgot Password
   ↓
2. User enters email on "Forgot Password" page
   ↓
3. POST /api/v1/auth/password-reset/request
   ↓
4. Backend creates reset token (1 hour expiration)
   ↓
5. Email sent with reset link
   ↓
6. User clicks link in email
   ↓
7. Frontend loads reset page with token from URL
   ↓
8. (Optional) POST /api/v1/auth/password-reset/verify to check token
   ↓
9. User enters new password
   ↓
10. POST /api/v1/auth/password-reset/confirm
    ↓
11. Password updated, token marked as used
    ↓
12. User automatically logged in with new tokens
    ↓
13. Redirect to dashboard
```

## API Endpoints

### 1. Request Password Reset

**Endpoint**: `POST /api/v1/auth/password-reset/request`

**Request**:
```json
{
  "email": "user@example.com"
}
```

**Response**: Always 200 OK (prevents email enumeration)
```json
{
  "message": "If the email exists, a password reset link has been sent",
  "detail": "Please check your email for instructions"
}
```

**Security**:
- Always returns success (even if email doesn't exist)
- Prevents attackers from discovering valid emails
- Invalidates all previous reset tokens for this user

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### 2. Verify Reset Token (Optional)

**Endpoint**: `POST /api/v1/auth/password-reset/verify`

**Purpose**: Validate token before showing reset form

**Request**:
```json
{
  "token": "abc123xyz789..."
}
```

**Response** (Success - 200 OK):
```json
{
  "message": "Token is valid",
  "valid": true
}
```

**Response** (Error - 400 Bad Request):
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_HERE"}'
```

### 3. Confirm Password Reset

**Endpoint**: `POST /api/v1/auth/password-reset/confirm`

**Request**:
```json
{
  "token": "abc123xyz789...",
  "new_password": "NewSecurePass123"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response** (Success - 200 OK):
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_admin": false,
    "company_id": "uuid",
    "created_at": "2025-10-25T...",
    "last_active": "2025-10-25T..."
  },
  "company": {
    "id": "uuid",
    "name": "Smith Law Firm",
    "plan_tier": "professional",
    "subscription_status": "active",
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

**Response** (Error - 400 Bad Request):
```json
{
  "detail": "Invalid or expired reset token"
}
```
or
```json
{
  "detail": "Reset token has already been used"
}
```
or
```json
{
  "detail": "Password must be at least 8 characters long"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN_HERE",
    "new_password": "NewSecurePass123"
  }'
```

## Frontend Integration Guide

### 1. Forgot Password Page

```typescript
async function requestPasswordReset(email: string) {
  try {
    const response = await api.post('/auth/password-reset/request', {
      email: email
    });

    // Always shows success message (security)
    alert('Password reset email sent. Please check your inbox.');

  } catch (error) {
    // Handle network errors
    alert('Something went wrong. Please try again.');
  }
}
```

### 2. Reset Password Page

**URL**: `/reset-password?token=abc123xyz789...`

```typescript
import { useSearchParams } from 'react-router-dom';

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [newPassword, setNewPassword] = useState('');
  const [isValidToken, setIsValidToken] = useState<boolean | null>(null);

  // Verify token on page load
  useEffect(() => {
    async function verifyToken() {
      if (!token) {
        setIsValidToken(false);
        return;
      }

      try {
        const response = await api.post('/auth/password-reset/verify', {
          token: token
        });
        setIsValidToken(response.data.valid);
      } catch (error) {
        setIsValidToken(false);
      }
    }

    verifyToken();
  }, [token]);

  async function handleResetPassword(e: FormEvent) {
    e.preventDefault();

    try {
      const response = await api.post('/auth/password-reset/confirm', {
        token: token,
        new_password: newPassword
      });

      // Store new tokens
      localStorage.setItem('access_token', response.data.token.access_token);
      localStorage.setItem('refresh_token', response.data.token.refresh_token);

      // Redirect to dashboard
      navigate('/dashboard');
      alert('Password reset successful!');

    } catch (error) {
      if (error.response?.status === 400) {
        alert(error.response.data.detail);
      } else {
        alert('Failed to reset password. Please try again.');
      }
    }
  }

  if (isValidToken === null) {
    return <div>Verifying token...</div>;
  }

  if (isValidToken === false) {
    return (
      <div>
        <h1>Invalid or Expired Link</h1>
        <p>This password reset link is invalid or has expired.</p>
        <a href="/forgot-password">Request a new reset link</a>
      </div>
    );
  }

  return (
    <form onSubmit={handleResetPassword}>
      <h1>Reset Your Password</h1>
      <input
        type="password"
        placeholder="New Password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
      />
      <button type="submit">Reset Password</button>
    </form>
  );
}
```

### 3. Email Link

The email contains a link like:
```
http://localhost:3000/reset-password?token=abc123xyz789...
```

In production:
```
https://yourdomain.com/reset-password?token=abc123xyz789...
```

## Security Features

### 1. Email Enumeration Prevention
**Problem**: Attackers could discover valid email addresses by checking which ones return "user not found"

**Solution**: Always return success, even if email doesn't exist
```python
# Always returns same success message
return {
    "message": "If the email exists, a password reset link has been sent",
    "detail": "Please check your email for instructions"
}
```

### 2. Token Hashing
**Problem**: If database is compromised, attacker could use tokens

**Solution**: Store SHA-256 hash, not plaintext
```python
token_hash = sha256(reset_token.encode()).hexdigest()
```

### 3. Short Expiration
**Problem**: Long-lived tokens increase attack window

**Solution**: 1-hour expiration
```python
expires_at = datetime.utcnow() + timedelta(hours=1)
```

### 4. One-Time Use
**Problem**: Token replay attacks

**Solution**: Mark token as used after successful reset
```python
db_token.is_used = True
db_token.used_at = datetime.utcnow()
```

### 5. Token Invalidation
**Problem**: Multiple active reset tokens could be confusing

**Solution**: Invalidate old tokens when new one is requested
```python
# Mark all existing tokens as used
for token in existing_tokens.scalars():
    token.is_used = True
```

### 6. Strong Password Validation
Enforced at schema level:
- Minimum 8 characters
- Uppercase + lowercase + digit required

## Testing

### Manual Testing with MailHog

1. **Start services**:
   ```bash
   docker-compose up -d
   ```

2. **Request password reset**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com"}'
   ```

3. **Check MailHog**:
   - Open http://localhost:8025
   - View the reset email
   - Copy the token from the reset link

4. **Verify token** (optional):
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/password-reset/verify \
     -H "Content-Type: application/json" \
     -d '{"token": "PASTE_TOKEN_HERE"}'
   ```

5. **Reset password**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
     -H "Content-Type: application/json" \
     -d '{
       "token": "PASTE_TOKEN_HERE",
       "new_password": "NewPassword123"
     }'
   ```

6. **Login with new password**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@example.com",
       "password": "NewPassword123"
     }'
   ```

### Expected Behaviors

✅ **Success Cases**:
- Request reset → Email sent
- Valid token → Verification succeeds
- Reset with valid token → Password changed, user logged in
- Login with new password → Success

❌ **Error Cases**:
- Invalid token → 400 "Invalid or expired reset token"
- Expired token (>1 hour) → 400 "Invalid or expired reset token"
- Already used token → 400 "Reset token has already been used"
- Weak password → 400 "Password must be at least 8 characters long"
- Non-existent email → Still returns success (security feature)

## Database Cleanup

Recommend adding a cron job to clean up old reset tokens:

```python
# Delete expired and used tokens older than 7 days
DELETE FROM password_reset_tokens
WHERE (is_used = TRUE OR expires_at < NOW())
AND created_at < NOW() - INTERVAL '7 days';
```

## Configuration

### Token Expiration

To change reset token expiration, edit in [backend/app/services/auth.py:375](../backend/app/services/auth.py#L375):

```python
# Default: 1 hour
expires_at = datetime.utcnow() + timedelta(hours=1)

# Change to 2 hours:
expires_at = datetime.utcnow() + timedelta(hours=2)

# Change to 30 minutes:
expires_at = datetime.utcnow() + timedelta(minutes=30)
```

### Password Requirements

To change password requirements, edit in [backend/app/schemas/auth.py:100-110](../backend/app/schemas/auth.py#L100-L110):

```python
@validator('new_password')
def validate_password(cls, v):
    if len(v) < 12:  # Change from 8 to 12
        raise ValueError('Password must be at least 12 characters long')
    # Add more rules as needed
    return v
```

## Next Steps

### Recommended Enhancements

1. **Rate Limiting**:
   - Limit reset requests per email (e.g., 1 per 5 minutes)
   - Prevent abuse

2. **Security Notifications**:
   - Send email when password is changed
   - Alert user of suspicious activity

3. **Multi-Factor Authentication**:
   - Require 2FA code for password reset
   - Extra security layer

4. **Account Recovery**:
   - Security questions as alternative
   - Support ticket for locked accounts

5. **Audit Logging**:
   - Log all password reset attempts
   - Monitor for suspicious patterns

## Completion Status

✅ **Milestone 1 - Task 4: COMPLETED**

The password reset flow is now fully implemented with:
- ✅ Database model with secure token storage
- ✅ Three API endpoints (request, verify, confirm)
- ✅ Email integration with professional templates
- ✅ Comprehensive security measures
- ✅ Token validation and expiration
- ✅ One-time use enforcement
- ✅ Email enumeration prevention
- ✅ Database migration
- ✅ Strong password validation

**Ready for**: Frontend integration and production deployment
