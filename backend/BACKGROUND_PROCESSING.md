# Background Processing Setup

This document explains how to set up and use the background task queue for automatic document processing.

## Overview

Documents uploaded to BC Legal Tech are now automatically processed through the full RAG pipeline:
1. **Text Extraction** - Extract text from PDF, DOCX, TXT files
2. **Chunking** - Split text into semantic chunks (respecting legal document structure)
3. **Embedding Generation** - Generate vector embeddings using OpenAI
4. **Vector Storage** - Store embeddings in PostgreSQL with pgvector

This processing happens **automatically in the background** after upload, powered by **Celery** and **Redis**.

---

## Prerequisites

### 1. Redis Installation

**Windows:**
- Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
- Or use Windows Subsystem for Linux (WSL) and install Redis via `sudo apt-get install redis-server`
- Or use Docker: `docker run --name redis -p 6379:6379 -d redis`

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### 2. Verify Redis is Running

Test connection:
```bash
redis-cli ping
# Should return: PONG
```

Or check if port 6379 is listening:
```bash
# Windows
netstat -an | findstr "6379"

# Mac/Linux
netstat -an | grep 6379
```

---

## Starting the Worker

### Method 1: Using the Batch Script (Windows)

1. Open a **new terminal window** (keep your FastAPI server running in another terminal)
2. Navigate to the backend directory:
   ```cmd
   cd C:\Users\alexs\projects\bc-legal-tech\backend
   ```
3. Run the Celery worker script:
   ```cmd
   start_celery_worker.bat
   ```

This will start a Celery worker that listens for document processing tasks.

### Method 2: Manual Command (Cross-Platform)

**Windows:**
```cmd
cd backend
venv\Scripts\activate
celery -A app.core.celery_app worker --loglevel=info --pool=solo --queues=document_processing
```

**Mac/Linux:**
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info --queues=document_processing
```

---

## How It Works

### Upload Flow

1. User uploads document via API (`POST /api/v1/documents/upload/quick`)
2. Document metadata is saved to database with `processing_status = 'pending'`
3. **Background task is triggered** (non-blocking)
4. API returns immediately with upload success
5. Celery worker picks up task and processes document:
   - Extracts text → status: `processing`
   - Chunks text → status: `chunked`
   - Generates embeddings → status: `embedded`
6. Document is now searchable via semantic search

### Task Monitoring

Check document processing status:
```bash
GET /api/v1/documents/{document_id}/processing-status
```

Response:
```json
{
  "document_id": "uuid",
  "document_title": "Employment Agreement.pdf",
  "processing_status": "embedded",
  "text_extracted": true,
  "indexed_for_search": true,
  "chunk_count": 12,
  "created_at": "2025-11-06T10:30:00",
  "updated_at": "2025-11-06T10:30:45",
  "status_description": "Ready for search"
}
```

### Status Values

- `pending` - Waiting to be processed
- `processing` - Currently extracting text and chunking
- `chunked` - Text chunked, generating embeddings
- `embedded` - **Ready for search** ✅
- `failed` - Processing failed, will retry (up to 3 times)

---

## Retry Behavior

Tasks automatically retry on failure:
- **Max retries**: 3
- **Retry delay**: 60 seconds (exponential backoff: 60s, 120s, 240s)
- **Task timeout**: 30 minutes (soft limit: 25 minutes)

If a task fails 3 times, it's marked as `failed` and can be retried manually by an admin.

---

## Development Workflow

### Running Locally

1. **Terminal 1** - Start PostgreSQL (Docker or local)
2. **Terminal 2** - Start Redis
   ```bash
   redis-server
   ```
3. **Terminal 3** - Start FastAPI server
   ```cmd
   cd backend
   venv\Scripts\activate
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Terminal 4** - Start Celery worker
   ```cmd
   cd backend
   venv\Scripts\activate
   celery -A app.core.celery_app worker --loglevel=info --pool=solo --queues=document_processing
   ```

### Testing Background Processing

1. Upload a document via API or test script
2. Watch Celery worker terminal for task execution logs
3. Check document status via processing-status endpoint
4. Verify document is searchable via semantic search

---

## Production Considerations

### Deployment

**Option 1: Managed Services**
- Use managed Redis (AWS ElastiCache, Redis Cloud, Upstash)
- Deploy Celery workers as separate containers/instances
- Scale workers horizontally based on queue depth

**Option 2: Docker Compose**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: ./backend
    command: celery -A app.core.celery_app worker --loglevel=info --queues=document_processing
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql+asyncpg://...
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Monitoring

1. **Celery Flower** - Web-based monitoring tool
   ```bash
   pip install flower
   celery -A app.core.celery_app flower
   ```
   Access at: http://localhost:5555

2. **Task Metrics** - Track:
   - Queue depth
   - Task success/failure rates
   - Average processing time
   - Worker health

3. **Alerts** - Set up alerts for:
   - High failure rate (> 10%)
   - Long queue depth (> 100 tasks)
   - Worker crashes
   - Redis unavailable

### Scaling

- Start with 2-4 workers per server
- Add workers based on queue depth monitoring
- Consider dedicated workers for different document types
- Use priority queues for urgent documents

---

## Troubleshooting

### Worker Won't Start

**Error**: `ModuleNotFoundError: No module named 'app'`
- **Fix**: Ensure you're in the `backend/` directory when starting worker
- **Fix**: Check that `PYTHONPATH` is set correctly

**Error**: `ConnectionError: Error connecting to Redis`
- **Fix**: Verify Redis is running (`redis-cli ping`)
- **Fix**: Check `REDIS_URL` in `.env` file
- **Fix**: Check firewall isn't blocking port 6379

### Tasks Not Processing

1. **Check worker is running**:
   ```bash
   celery -A app.core.celery_app inspect active
   ```

2. **Check queue depth**:
   ```bash
   celery -A app.core.celery_app inspect reserved
   ```

3. **Check task was registered**:
   ```bash
   celery -A app.core.celery_app inspect registered
   ```

4. **Check worker logs** for errors

### Tasks Failing

1. Check worker logs for detailed error messages
2. Verify OpenAI API key is set in `.env`
3. Verify database connection from worker
4. Check document file is accessible in S3/storage
5. Test processing manually via `test_embedding_pipeline.py`

---

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

### Celery Settings

Located in `app/core/celery_app.py`:

```python
celery_app.conf.update(
    task_track_started=True,           # Track when tasks start
    task_time_limit=30 * 60,           # 30 minutes max per task
    task_soft_time_limit=25 * 60,      # 25 minutes soft limit
    task_acks_late=True,               # Acknowledge after completion
    worker_prefetch_multiplier=1,      # Take one task at a time
    worker_max_tasks_per_child=50,     # Restart after 50 tasks (prevent memory leaks)
)
```

---

## Next Steps

1. ✅ Background processing implemented
2. ⬜ Add admin endpoint to retry failed tasks
3. ⬜ Add Celery Flower for monitoring
4. ⬜ Add task result webhooks (notify when processing complete)
5. ⬜ Add priority queue for urgent documents
6. ⬜ Add batch processing for bulk uploads

---

## Related Files

- `app/core/celery_app.py` - Celery configuration
- `app/tasks/document_processing.py` - Background task definitions
- `app/api/v1/endpoints/documents.py` - Upload endpoints (trigger tasks)
- `start_celery_worker.bat` - Worker startup script (Windows)

---

**Status**: ✅ Background processing ready for testing
**Last Updated**: 2025-11-06
