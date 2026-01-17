# Running the Backend - Complete Guide

## Quick Start (Fastest Way)

### 1. Start Docker Services

```bash
docker-compose up -d
```

This starts:

- PostgreSQL (port 5432)
- Valkey (port 6379)
- LocalStack/S3 (port 4566)
- MailHog (ports 1025, 8025)

### 2. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 3. Start Backend Server

**Option A: Direct Python**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Option B: With Virtual Environment (Recommended)**

```bash
cd backend
# Activate venv (if not already activated)
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies in venv first (if not done)
pip install -r requirements.txt

# Start server using python -m to ensure correct module resolution
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Verify It's Running

Open browser: http://localhost:8000/docs

You should see the Swagger API documentation.

Or test with curl:

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

---

## Detailed Setup

### Prerequisites

1. **Docker Desktop** - Running
2. **Python 3.10+** - Installed
3. **Git** - For cloning repository

### First Time Setup

#### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Variables (Optional)

Create `backend/.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sred_dev

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Email (MailHog for development)
SMTP_HOST=localhost
SMTP_PORT=1025
EMAIL_FROM=noreply@pendingdomain.com
EMAIL_FROM_NAME=SR&ED

# AWS/S3 (LocalStack)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=ca-central-1
S3_BUCKET_NAME=sred-documents

# App
ENVIRONMENT=development
DEBUG=true
```

**Note**: The app works with default values, `.env` is optional.

#### 3. Start Docker Services

```bash
docker-compose up -d
```

Wait 5-10 seconds for services to initialize.

#### 4. Verify Docker Services

```bash
docker ps
```

You should see:

```
CONTAINER ID   IMAGE                      STATUS   PORTS
xxxxx          pgvector/pgvector:pg15     Up       0.0.0.0:5432->5432/tcp
xxxxx          valkey/valkey:8-alpine     Up       0.0.0.0:6379->6379/tcp
xxxxx          localstack/localstack      Up       0.0.0.0:4566->4566/tcp
xxxxx          mailhog/mailhog           Up       0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
```

#### 5. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_refresh_tokens
INFO  [alembic.runtime.migration] Running upgrade 001_refresh_tokens -> 002_password_reset
```

#### 6. Start Backend Server

```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```

Expected output:

```
INFO:     Will watch for changes in these directories: ['C:\\...\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 7. Test the Server

**Browser**: http://localhost:8000/docs

**Curl**:

```bash
curl http://localhost:8000/health
```

---

## Running for Development

### Terminal 1: Docker Services

```bash
docker-compose up
```

Leave this running (without `-d` flag to see logs).

### Terminal 2: Backend Server

```bash
cd backend
.\venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables auto-restart on code changes.

### Terminal 3: Testing

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Test","admin_email":"test@test.com","admin_password":"Password123"}'

# Or run test script
cd backend
python test_email.py
```

---

## Useful Commands

### Check Service Status

```bash
# All containers
docker ps

# Specific service logs
docker logs sred-postgres
docker logs sred-mailhog
```

### Database Operations

```bash
cd backend

# Check current migration version
alembic current

# Run all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Create new migration (auto-generate)
alembic revision --autogenerate -m "Description"
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart postgres
docker-compose restart mailhog

# Stop all
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### View Logs

```bash
# Backend logs (in console where uvicorn is running)

# Docker service logs
docker-compose logs -f postgres
docker-compose logs -f mailhog

# All services
docker-compose logs -f
```

---

## Accessing Services

| Service       | URL/Port                    | Purpose              |
| ------------- | --------------------------- | -------------------- |
| Backend API   | http://localhost:8000       | Main API             |
| Swagger Docs  | http://localhost:8000/docs  | Interactive API docs |
| ReDoc         | http://localhost:8000/redoc | Alternative API docs |
| MailHog UI    | http://localhost:8025       | View sent emails     |
| PostgreSQL    | localhost:5432              | Database             |
| Valkey        | localhost:6379              | Cache/task queue     |
| LocalStack/S3 | localhost:4566              | S3 storage           |

### Database Connection

```
Host: localhost
Port: 5432
Database: sred_dev
Username: postgres
Password: postgres
```

**Connection String**:

```
postgresql://postgres:postgres@localhost:5432/sred_dev
```

---

## Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solution**:

```bash
# Windows - Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Cannot Connect to Database

**Check if PostgreSQL is running**:

```bash
docker ps | grep postgres
```

**Restart PostgreSQL**:

```bash
docker-compose restart postgres
```

**Check connection**:

```bash
# Windows
docker exec -it <container_id> psql -U postgres -d sred_dev

# Or use any PostgreSQL client
psql -h localhost -U postgres -d sred_dev
```

### Migration Errors

**Error**: `Target database is not up to date`

**Solution**:

```bash
cd backend
alembic upgrade head
```

**Error**: `Can't locate revision identified by 'xxx'`

**Solution** (nuclear option - only for development):

```bash
# Drop database and recreate
docker-compose down -v
docker-compose up -d
# Wait 10 seconds
cd backend
alembic upgrade head
```

### Module Not Found Errors

**Error**: `ModuleNotFoundError: No module named 'app'` or `ModuleNotFoundError: No module named 'asyncpg'`

**Solution**: Make sure you're in the `backend` directory and dependencies are installed:

```bash
cd backend

# Option 1: Use python -m (works without venv activation)
python -m uvicorn app.main:app --reload --port 8000

# Option 2: Activate venv and install dependencies
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Why `python -m uvicorn`?** This ensures Python uses the correct module search path and finds all installed packages, avoiding path-related issues especially on Windows.

### MailHog Not Receiving Emails

**Check if MailHog is running**:

```bash
docker ps | grep mailhog
```

**Restart MailHog**:

```bash
docker-compose restart mailhog
```

**Test SMTP connection**:

```bash
telnet localhost 1025
```

### "Unhealthy" Database

**Check logs**:

```bash
docker logs sred-postgres
```

**Recreate container**:

```bash
docker-compose down
docker-compose up -d
```

---

## Production Deployment

For production, use a proper ASGI server setup:

### With Gunicorn + Uvicorn Workers

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Environment Variables for Production

```bash
# REQUIRED: Change these!
JWT_SECRET_KEY=<strong-random-secret-key>
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/dbname

# Email - Use real SMTP
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<your-sendgrid-api-key>
SMTP_TLS=true
EMAIL_FROM=noreply@yourdomain.com

# AWS - Use real credentials
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
AWS_ENDPOINT_URL=  # Leave empty for real AWS
AWS_REGION=ca-central-1
S3_BUCKET_NAME=your-prod-bucket

# App
ENVIRONMENT=production
DEBUG=false
```

---

## Quick Reference

### Start Everything (Fresh)

```bash
# 1. Start Docker
docker-compose up -d

# 2. Run migrations
cd backend
alembic upgrade head

# 3. Start backend
uvicorn app.main:app --reload --port 8000

# 4. Test
curl http://localhost:8000/health
```

### Stop Everything

```bash
# Stop backend: Ctrl+C in terminal

# Stop Docker services
docker-compose down
```

### Reset Everything (Clean Slate)

```bash
# Stop and remove everything including data
docker-compose down -v

# Start fresh
docker-compose up -d

# Wait 10 seconds, then migrate
cd backend
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

---

## Development Workflow

### Typical Development Session

```bash
# 1. Start Docker (morning)
docker-compose up -d

# 2. Start backend with auto-reload
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 3. Code changes (auto-reloads)
# Edit files in backend/app/...

# 4. Test changes
# Use Postman/curl/Swagger

# 5. When done (evening)
# Ctrl+C to stop backend
docker-compose down
```

### Making Database Changes

```bash
# 1. Edit models in backend/app/models/models.py

# 2. Create migration
cd backend
alembic revision --autogenerate -m "Add new table"

# 3. Review migration file in backend/alembic/versions/

# 4. Apply migration
alembic upgrade head

# 5. Backend auto-reloads with new models
```

---

## Testing the Setup

After starting everything, run this quick test:

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Firm",
    "admin_email": "test@example.com",
    "admin_password": "TestPass123",
    "admin_first_name": "Test",
    "admin_last_name": "User"
  }'

# Test 3: Check MailHog
# Open http://localhost:8025 (should see no emails yet)

# Test 4: Request password reset
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test 5: Check MailHog again
# Open http://localhost:8025 (should see password reset email!)
```

If all tests pass, you're ready to develop! 🚀

---

## Next Steps

1. ✅ Backend is running
2. ✅ Docker services are up
3. ✅ Database is migrated
4. ✅ Can access Swagger at http://localhost:8000/docs

Now you can:

- Use Postman collection to test endpoints
- Run automated tests
- Start developing new features
- Test with frontend (when ready)

**See also**:

- [Testing Guide](./TESTING-GUIDE.md) - Complete testing walkthrough
- [Postman Collection](../postman/sred-Tech.postman_collection.json) - Import into Postman
