# Refresh Token Implementation

## Overview

This document describes the refresh token implementation for BC Legal Tech's authentication system.

## What Was Implemented

### 1. Database Model
**File**: [backend/app/models/models.py](../backend/app/models/models.py)

Created `RefreshToken` model with:
- `id`: Unique identifier (UUID)
- `user_id`: Foreign key to users table
- `token_hash`: SHA-256 hash of the refresh token (for secure storage)
- `expires_at`: Expiration timestamp (30 days by default)
- `is_revoked`: Boolean flag for token revocation
- `created_at`: Token creation timestamp
- `revoked_at`: Token revocation timestamp (nullable)

**Security Features**:
- Tokens are stored as SHA-256 hashes, not plaintext
- Indexed on `token_hash` for fast lookups
- Indexed on `user_id` for user-level queries

### 2. Configuration
**File**: [backend/app/core/config.py](../backend/app/core/config.py:25)

Added:
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30` (30-day refresh token lifetime)

### 3. Schemas
**File**: [backend/app/schemas/auth.py](../backend/app/schemas/auth.py)

Updated:
- `Token` schema: Added optional `refresh_token` field
- `RefreshTokenRequest` schema: New schema for refresh endpoint request

### 4. Authentication Utilities
**File**: [backend/app/utils/auth.py](../backend/app/utils/auth.py)

Added functions:
- `create_refresh_token_jwt()`: Creates JWT refresh token with 30-day expiration
- `hash_refresh_token()`: Creates SHA-256 hash of token for storage
- Added imports: `secrets`, `hashlib`

### 5. Authentication Service
**File**: [backend/app/services/auth.py](../backend/app/services/auth.py)

Added methods:
- `create_refresh_token(user)`: Creates and stores refresh token in database
- `verify_refresh_token(token)`: Validates refresh token and returns user
- `revoke_refresh_token(token)`: Revokes a refresh token

**Security Features**:
- Token rotation: Old refresh token is revoked when used
- Multiple validation checks:
  - JWT signature and expiration
  - Token type verification (must be "refresh" type)
  - Database lookup verification
  - Revocation status check
  - Manual expiration check
  - User active status check

### 6. API Endpoints
**File**: [backend/app/api/v1/endpoints/auth.py](../backend/app/api/v1/endpoints/auth.py)

Updated endpoints:
- `POST /api/v1/auth/register`: Now returns refresh token
- `POST /api/v1/auth/login`: Now returns refresh token
- `POST /api/v1/auth/refresh`: **NEW** - Implemented refresh token endpoint

### 7. Database Migration
**File**: [backend/alembic/versions/001_add_refresh_tokens_table.py](../backend/alembic/versions/001_add_refresh_tokens_table.py)

Created migration to add `refresh_tokens` table with indexes.

## How It Works

### Token Lifecycle

1. **Login/Register**:
   ```
   POST /api/v1/auth/login
   Response:
   {
     "user": {...},
     "company": {...},
     "token": {
       "access_token": "eyJ...",
       "refresh_token": "eyJ...",
       "token_type": "bearer",
       "expires_in": 1800
     }
   }
   ```

2. **Access Token Expires** (after 30 minutes):
   - Frontend detects 401 error or expired token
   - Frontend calls refresh endpoint with refresh token

3. **Refresh Token**:
   ```
   POST /api/v1/auth/refresh
   Body: {
     "refresh_token": "eyJ..."
   }
   Response:
   {
     "access_token": "eyJ... (new)",
     "refresh_token": "eyJ... (new)",
     "token_type": "bearer",
     "expires_in": 1800
   }
   ```

4. **Token Rotation** (Security Feature):
   - Old refresh token is revoked
   - New refresh token is issued
   - This prevents replay attacks

### Security Model

1. **Short-lived Access Tokens** (30 minutes):
   - Minimizes exposure if token is compromised
   - Not stored in database (stateless JWT)

2. **Long-lived Refresh Tokens** (30 days):
   - Stored in database as SHA-256 hash
   - Can be revoked server-side
   - Rotated on every use

3. **Token Rotation**:
   - Each refresh creates new tokens
   - Old refresh token is immediately revoked
   - Prevents token replay attacks

4. **Revocation Support**:
   - Refresh tokens can be revoked (e.g., on logout, password change)
   - Revoked tokens cannot be used
   - Future: Add endpoint to revoke all user tokens

## Frontend Integration Guide

### 1. Store Tokens
```typescript
// After login/register
const response = await api.post('/auth/login', credentials);
localStorage.setItem('access_token', response.data.token.access_token);
localStorage.setItem('refresh_token', response.data.token.refresh_token);
```

### 2. Attach Access Token to Requests
```typescript
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 3. Handle Token Expiration
```typescript
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });

        // Store new tokens
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### 4. Logout
```typescript
async function logout() {
  // TODO: Add /auth/logout endpoint that revokes refresh token
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}
```

## Testing the Implementation

### Manual Test with curl

1. **Register/Login**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "YourPassword123"
  }'
```

Save the `access_token` and `refresh_token` from response.

2. **Use Access Token**:
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. **Refresh Token**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Expected Behavior

✅ **Success Cases**:
- Login returns both access and refresh tokens
- Refresh endpoint returns new tokens
- Old refresh token cannot be reused (revoked)
- New tokens work correctly

❌ **Error Cases**:
- Using revoked refresh token → 401 "Refresh token has been revoked"
- Using expired refresh token → 401 "Refresh token has expired"
- Using invalid refresh token → 401 "Invalid or expired refresh token"
- Using access token on refresh endpoint → 401 "Invalid token type"

## Next Steps

### Recommended Enhancements

1. **Logout Endpoint Enhancement**:
   - Update `/auth/logout` to revoke refresh token
   - Add "revoke all sessions" functionality

2. **Session Management**:
   - Add endpoint to list active sessions (refresh tokens)
   - Add endpoint to revoke specific sessions
   - Add endpoint to revoke all sessions

3. **Security Hardening**:
   - Add rate limiting on refresh endpoint
   - Add device/IP tracking for refresh tokens
   - Alert user on new device login
   - Add suspicious activity detection

4. **Monitoring**:
   - Log refresh token usage
   - Monitor for unusual patterns
   - Alert on multiple failed refresh attempts

5. **Database Cleanup**:
   - Add cron job to delete expired/revoked tokens
   - Prevent database bloat

## Database Migration

To apply the refresh token table:

```bash
cd backend
alembic upgrade head
```

Or use the project's migration command:
```bash
/db-migrate "Add refresh tokens table"
```

## Completion Status

✅ **Milestone 1 - Task 3: COMPLETED**

The refresh token endpoint is now fully implemented with:
- ✅ Database model
- ✅ Token creation and storage
- ✅ Token validation
- ✅ Token rotation (security best practice)
- ✅ Revocation support
- ✅ Database migration
- ✅ API endpoint
- ✅ Comprehensive error handling
- ✅ Security measures (hashing, expiration, type checking)

**Ready for**: Frontend integration and testing
