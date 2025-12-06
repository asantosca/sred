# BC Legal Tech - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- ✅ Docker Desktop (running)
- ✅ Python 3.10+ (installed)
- ✅ Git (installed)

## Method 1: One-Click Start (Easiest)

### Windows

```bash
# Just double-click or run:
.\start-backend.bat
```

This will:

1. ✅ Check Docker is running
2. ✅ Start all Docker services
3. ✅ Run database migrations
4. ✅ Start backend server

**Done!** Server runs at http://localhost:8000

### Manual Commands

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Run migrations
cd backend
alembic upgrade head

# 3. Start server
uvicorn app.main:app --reload --port 8000
```

---

## Method 2: Test with Postman (Best for API Testing)

### 1. Start Backend

```bash
.\start-backend.bat
```

### 2. Import Postman Collection

1. Open Postman
2. Click **Import**
3. Drag `postman/BC-Legal-Tech.postman_collection.json`
4. Drag `postman/BC-Legal-Tech.postman_environment.json`
5. Select environment: "BC Legal Tech - Development" (top right)

### 3. Test Endpoints

**Quick Test Sequence**:

1. Health Check ✓
2. Register Company ✓ (saves tokens automatically)
3. Get Current User ✓
4. Login ✓
5. Refresh Token ✓

**See**: [postman/README.md](postman/README.md) for detailed guide

---

## Method 3: Interactive API Docs (Swagger)

### 1. Start Backend

```bash
.\start-backend.bat
```

### 2. Open Swagger

http://localhost:8000/docs

### 3. Test Endpoints

1. Click endpoint to expand
2. Click **"Try it out"**
3. Fill in request body
4. Click **"Execute"**
5. See response below

**For Protected Endpoints** (like `/auth/me`):

1. First run `/auth/register` or `/auth/login`
2. Copy `access_token` from response
3. Click 🔓 **"Authorize"** button at top
4. Enter: `Bearer YOUR_ACCESS_TOKEN`
5. Click **"Authorize"**
6. Now test protected endpoints

---

## Important URLs

| Service          | URL                         | Purpose                 |
| ---------------- | --------------------------- | ----------------------- |
| **Backend API**  | http://localhost:8000       | Main API server         |
| **Swagger Docs** | http://localhost:8000/docs  | Interactive API testing |
| **MailHog UI**   | http://localhost:8025       | View sent emails        |
| **ReDoc**        | http://localhost:8000/redoc | Alternative API docs    |

---

## Quick Test Examples

### Test 1: Register & Login (curl)

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Law Firm",
    "admin_email": "admin@test.com",
    "admin_password": "Password123",
    "admin_first_name": "John",
    "admin_last_name": "Doe"
  }'

# Copy access_token from response

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test 2: Password Reset Flow

```bash
# 1. Request reset
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com"}'

# 2. Check MailHog at http://localhost:8025

# 3. Copy token from email link

# 4. Reset password
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "PASTE_TOKEN_HERE",
    "new_password": "NewPassword456"
  }'

# 5. Login with new password
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "NewPassword456"
  }'
```

### Test 3: Email Service

```bash
cd backend
python test_email.py

# View emails at http://localhost:8025
```

---

## Troubleshooting

### "Could not connect to database"

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart services
docker-compose restart postgres
```

### "Port 8000 already in use"

```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### "MailHog not receiving emails"

```bash
# Check MailHog is running
docker ps | grep mailhog

# Restart MailHog
docker-compose restart mailhog

# Access at http://localhost:8025
```

### "Module not found" errors

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Next Steps

### After Testing

1. ✅ All endpoints work
2. ✅ Understand API structure
3. ✅ Ready to build more features

### Continue Development

**Complete Milestone 1** (2 tasks remaining):

- [ ] User profile update endpoint
- [ ] User avatar upload

**Start Milestone 2** (Document Management):

- [ ] Document upload API
- [ ] Document listing
- [ ] Document download/preview
- [ ] S3 integration

---

## Documentation

**Getting Started**:

- 📖 [Running Backend](docs/RUNNING-BACKEND.md) - Detailed setup guide
- 📖 [Testing Guide](docs/TESTING-GUIDE.md) - Complete testing walkthrough
- 📖 [Postman Guide](postman/README.md) - Postman collection usage

**Features**:

- 📖 [Refresh Tokens](docs/refresh-token-implementation.md)
- 📖 [Password Reset](docs/password-reset-implementation.md)
- 📖 [Email Service](docs/email-service-setup.md)
- 📖 [Email Quick Start](docs/QUICKSTART-EMAIL.md)

**Project**:

- 📖 [Implementation Status](docs/IMPLEMENTATION-STATUS.md) - What's built
- 📖 [Roadmap](ROADMAP.md) - Full project plan

---

## Common Commands

```bash
# Start everything
docker-compose up -d
cd backend && alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Or use quick start script
.\start-backend.bat

# Stop everything
# Ctrl+C (stop backend)
docker-compose down

# View logs
docker-compose logs -f

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
cd backend && alembic upgrade head

# Run tests
cd backend && python test_email.py
.\test-everything.bat
```

---

## Support

**Issues?** Check these first:

1. Is Docker running? → `docker ps`
2. Are services up? → `docker-compose ps`
3. Is backend running? → `curl http://localhost:8000/health`
4. Check logs → `docker-compose logs`

**Documentation**: See `docs/` folder for detailed guides

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ BC Legal Tech - Quick Reference                        │
├─────────────────────────────────────────────────────────┤
│ Start Backend:    .\start-backend.bat                  │
│ API Docs:         http://localhost:8000/docs           │
│ MailHog:          http://localhost:8025                │
│ Test Emails:      cd backend && python test_email.py   │
│ Postman:          Import postman/*.json                │
│ Stop:             Ctrl+C, then docker-compose down     │
└─────────────────────────────────────────────────────────┘
```

**Ready to start!** 🚀

Run: `.\start-backend.bat`

Then open: http://localhost:8000/docs
