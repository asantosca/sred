# BC Legal Tech - Postman Collection

Complete Postman collection for testing BC Legal Tech API.

## Quick Start

### 1. Import Collection

1. Open Postman
2. Click "Import" button
3. Drag and drop `BC-Legal-Tech.postman_collection.json`
4. Collection will appear in sidebar

### 2. Import Environment

1. Click "Environments" in sidebar
2. Click "Import"
3. Drag and drop `BC-Legal-Tech.postman_environment.json`
4. Select "BC Legal Tech - Development" from environment dropdown (top right)

### 3. Start Backend Server

```bash
# Terminal 1: Start Docker
docker-compose up -d

# Terminal 2: Start Backend
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Run Requests

Execute requests in this order:

1. **Health Check** - Verify server is running
2. **Register Company** - Create account (saves tokens automatically)
3. **Get Current User** - Test JWT authentication
4. **Login** - Test login flow
5. **Refresh Token** - Test token refresh
6. **Request Password Reset** - Test password reset flow
7. Check MailHog at http://localhost:8025 for reset email
8. Copy token from email and paste into environment variable `reset_token`
9. **Verify Reset Token** - Check token validity
10. **Confirm Password Reset** - Complete reset

---

## Collection Structure

### Authentication
- **Register Company** - Create new company with admin user
- **Login** - Authenticate with email/password
- **Get Current User** - Get authenticated user info (requires token)
- **Refresh Token** - Get new access token
- **Logout** - Logout user

### Password Reset
- **Request Password Reset** - Send reset email
- **Verify Reset Token** - Check token validity
- **Confirm Password Reset** - Reset password with token

### Health Check
- **Health Check** - Verify API is running

---

## Environment Variables

The collection uses these environment variables:

### Configuration
- `base_url` - API base URL (default: http://localhost:8000)
- `company_name` - Company name for registration
- `admin_email` - Admin email for registration
- `admin_password` - Admin password
- `admin_first_name` - Admin first name
- `admin_last_name` - Admin last name

### Auto-Populated (by tests)
- `access_token` - JWT access token (auto-saved from login/register)
- `refresh_token` - Refresh token (auto-saved)
- `user_id` - Current user ID (auto-saved)
- `company_id` - Current company ID (auto-saved)

### Manual
- `reset_token` - Password reset token (copy from email in MailHog)

---

## Features

### Automatic Token Management
The collection automatically saves tokens to environment variables:
- Register → Saves access_token and refresh_token
- Login → Updates tokens
- Refresh → Updates tokens
- Password Reset Confirm → Updates tokens

No need to manually copy/paste tokens!

### Test Scripts
Each request includes test scripts that:
- Verify response status codes
- Check response structure
- Save tokens to environment
- Display helpful console messages

### Pre-Configured
All requests are pre-configured with:
- Correct headers
- Request body templates
- Authentication (where needed)
- Environment variable substitution

---

## Usage Examples

### Test Complete Registration Flow

1. Click "Register Company"
2. Click "Send"
3. Check response - should see user, company, and tokens
4. Click "Get Current User"
5. Click "Send"
6. Should return same user info (proves JWT works)

### Test Password Reset Flow

1. Click "Request Password Reset"
2. Click "Send"
3. Open http://localhost:8025 (MailHog)
4. Open the password reset email
5. Find the reset link: `http://localhost:3000/reset-password?token=ABC123...`
6. Copy the token (the part after `token=`)
7. In Postman, go to Environments → BC Legal Tech - Development
8. Set `reset_token` to the copied token
9. Click "Verify Reset Token" → Send (should return valid: true)
10. Click "Confirm Password Reset" → Send
11. Password is now reset to "NewPassword123"
12. Try "Login" with new password

### Test Token Refresh

1. Click "Login" to get fresh tokens
2. Click "Refresh Token"
3. Click "Send"
4. New tokens are automatically saved
5. Try "Get Current User" with new token

### Test Token Rotation (Security Feature)

1. Click "Login" to get tokens
2. Copy the `refresh_token` value
3. Click "Refresh Token" → Send (works, returns new tokens)
4. Paste the OLD refresh token back into environment
5. Click "Refresh Token" → Send again
6. Should get 401 error: "Refresh token has been revoked"

This proves token rotation security works!

---

## Tips

### View Console Output

Open Postman Console (View → Show Postman Console) to see:
- "✓ Tokens saved to environment"
- "✓ Password reset successful"
- Other helpful messages

### Run Multiple Requests

Use Postman Collection Runner:
1. Right-click collection
2. Click "Run collection"
3. Select requests to run
4. Click "Run BC Legal Tech API"
5. See all results at once

### Test Against Different Environments

Create multiple environments:
- Development (localhost:8000)
- Staging (staging.yourapp.com)
- Production (api.yourapp.com)

Switch between them using the environment dropdown.

### Save Requests

Use "Save Response" to:
- Keep examples of successful responses
- Document expected behavior
- Share with team

---

## Troubleshooting

### "Could not send request"

**Problem**: Backend not running

**Solution**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### "401 Unauthorized" on Get Current User

**Problem**: Access token expired or invalid

**Solution**:
1. Run "Login" again to get fresh tokens
2. Verify `access_token` is set in environment

### "Invalid or expired reset token"

**Problem**: Reset token expired (1 hour) or already used

**Solution**:
1. Run "Request Password Reset" again
2. Get new token from MailHog
3. Update `reset_token` in environment

### Tokens not saving automatically

**Problem**: Test scripts not running

**Solution**:
1. Check Postman Console for errors
2. Ensure environment is selected (top right)
3. Verify "BC Legal Tech - Development" is active

### Can't find reset email in MailHog

**Problem**: MailHog not running or email failed

**Solution**:
```bash
# Check MailHog
docker ps | grep mailhog

# Restart if needed
docker-compose restart mailhog

# Check at http://localhost:8025
```

---

## Customization

### Change Test User Details

Edit environment variables:
- `admin_email` - Change email address
- `admin_password` - Change password
- `company_name` - Change company name

### Add New Requests

1. Right-click folder (e.g., "Authentication")
2. Click "Add Request"
3. Configure request
4. Add test scripts if needed
5. Save

### Duplicate for Testing

Right-click any request → Duplicate

Useful for:
- Testing different payloads
- Testing error cases
- Creating variations

---

## Request Order

For best results, run requests in this order:

### First Time Setup
1. Health Check
2. Register Company (saves tokens)
3. Get Current User (tests auth)

### Normal Testing
1. Login (get fresh tokens)
2. Get Current User
3. Refresh Token (optional)
4. Other requests...

### Password Reset Testing
1. Request Password Reset
2. Check MailHog (http://localhost:8025)
3. Copy token to environment
4. Verify Reset Token
5. Confirm Password Reset
6. Login with new password

---

## Advanced Usage

### Collection Variables

Set variables at collection level:
- Right-click collection → Edit
- Go to Variables tab
- Add variables available to all requests

### Pre-request Scripts

Add setup code that runs before request:
```javascript
// Example: Generate random email
pm.environment.set('random_email',
  'user' + Math.floor(Math.random() * 10000) + '@test.com'
);
```

### Chain Requests

Use test scripts to chain requests:
```javascript
// After register, automatically run login
if (pm.response.code === 201) {
    postman.setNextRequest("Login");
}
```

---

## Export & Share

### Export Collection
1. Right-click collection
2. Click "Export"
3. Choose Collection v2.1
4. Save JSON file
5. Share with team

### Export Environment
1. Click Environments
2. Click ••• next to environment
3. Click "Export"
4. Save JSON file
5. Share with team

---

## Next Steps

After testing with Postman:

1. ✅ Verify all endpoints work
2. ✅ Understand request/response structure
3. ✅ Ready to integrate with frontend
4. ✅ Ready to write automated tests
5. ✅ Ready to build more features

---

## Resources

- **API Documentation**: http://localhost:8000/docs (Swagger)
- **MailHog UI**: http://localhost:8025
- **Collection File**: `BC-Legal-Tech.postman_collection.json`
- **Environment File**: `BC-Legal-Tech.postman_environment.json`
- **Testing Guide**: [../docs/TESTING-GUIDE.md](../docs/TESTING-GUIDE.md)
- **Running Backend**: [../docs/RUNNING-BACKEND.md](../docs/RUNNING-BACKEND.md)

---

**Happy Testing!** 🚀
