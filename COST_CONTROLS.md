# Cost Controls & Usage Limits

Protection against runaway AWS/AI API costs during development and beta testing.

---

## Philosophy

**No payments until we have customers. Focus on quality, but prevent cost explosions.**

---

## Cost Sources (Ranked by Risk)

### 🔴 **HIGH RISK - Immediate Action Required**

1. **OpenAI/Voyage AI Embeddings**
   - Cost: ~$0.13 per 1M tokens (OpenAI text-embedding-3-small)
   - Risk: Processing large PDFs can burn through tokens fast
   - Example: 1000-page contract = ~500K tokens = $0.065 per document
   - **At scale**: 1000 documents = $65

2. **Claude API (Chat)**
   - Cost: $3 per 1M input tokens, $15 per 1M output tokens
   - Risk: Long conversations with large context windows
   - Example: 10K tokens context + 500 tokens response = $0.0375 per query
   - **At scale**: 1000 queries/day = $37.50/day = $1125/month

3. **PostgreSQL PGvector**
   - Cost: Minimal for small datasets, but scales with storage
   - Risk: Vector storage (1536 dims × 8 bytes = 12KB per embedding)
   - Example: 1M chunks = 12GB just for embeddings

### 🟡 **MEDIUM RISK - Monitor**

4. **S3 Storage**
   - Cost: $0.023 per GB/month
   - Risk: Document storage accumulation
   - Example: 10GB documents = $0.23/month (negligible)

5. **Data Transfer**
   - Cost: $0.09 per GB outbound
   - Risk: Downloading large documents frequently
   - Example: 100GB downloads = $9/month

### 🟢 **LOW RISK**

6. **RDS PostgreSQL**
   - Cost: Fixed (LocalStack free in dev)
7. **Redis**
   - Cost: Fixed (LocalStack free in dev)

---

## Hard Limits Strategy

### Phase 1: Development (Current)
**Goal:** Prevent accidental $1000+ bills during testing

### Phase 2: Beta Testing
**Goal:** Support 10-50 test users without breaking the bank

### Phase 3: Launch (When Customers Arrive)
**Goal:** Usage-based soft limits, upgrade prompts

---

## Implementation Plan

### 1. Database Schema for Limits

```sql
-- Already exists in companies table:
-- plan_tier: 'starter', 'professional', 'enterprise'

-- Add usage tracking columns to companies table
ALTER TABLE companies ADD COLUMN IF NOT EXISTS usage_documents_count INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS usage_storage_bytes BIGINT DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS usage_ai_queries_count INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS usage_embeddings_count INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS usage_reset_date DATE;

-- Create plan_limits table (configurable limits)
CREATE TABLE plan_limits (
  plan_tier VARCHAR(50) PRIMARY KEY,
  max_documents INTEGER NOT NULL,
  max_storage_gb INTEGER NOT NULL,
  max_ai_queries_per_month INTEGER NOT NULL,
  max_document_size_mb INTEGER NOT NULL,
  max_users INTEGER NOT NULL,
  allow_embeddings BOOLEAN DEFAULT true,
  allow_ocr BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE
);

-- Insert default limits (conservative for beta)
INSERT INTO plan_limits (plan_tier, max_documents, max_storage_gb, max_ai_queries_per_month, max_document_size_mb, max_users) VALUES
('free', 50, 1, 100, 10, 1),           -- Solo lawyer testing
('starter', 500, 10, 1000, 50, 5),     -- Small firm
('professional', 5000, 100, 10000, 50, 25),  -- Mid-size firm
('enterprise', -1, -1, -1, 100, -1);   -- Unlimited (-1 = no limit)
```

### 2. Usage Tracking Service

**File:** `backend/app/services/usage_tracker.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import date
from uuid import UUID

class UsageTracker:
    """Track and enforce usage limits"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_document_limit(self, company_id: UUID) -> bool:
        """Check if company can upload more documents"""
        result = await self.db.execute("""
            SELECT
                c.usage_documents_count,
                pl.max_documents
            FROM companies c
            JOIN plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = $1
        """, company_id)

        row = result.first()
        if not row:
            return False

        current, max_allowed = row
        if max_allowed == -1:  # Unlimited
            return True

        return current < max_allowed

    async def check_storage_limit(self, company_id: UUID, file_size_bytes: int) -> bool:
        """Check if company has storage space"""
        result = await self.db.execute("""
            SELECT
                c.usage_storage_bytes,
                pl.max_storage_gb
            FROM companies c
            JOIN plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = $1
        """, company_id)

        row = result.first()
        current_bytes, max_gb = row

        if max_gb == -1:  # Unlimited
            return True

        max_bytes = max_gb * 1024 * 1024 * 1024
        return (current_bytes + file_size_bytes) <= max_bytes

    async def check_ai_query_limit(self, company_id: UUID) -> bool:
        """Check if company can make more AI queries this month"""
        result = await self.db.execute("""
            SELECT
                c.usage_ai_queries_count,
                c.usage_reset_date,
                pl.max_ai_queries_per_month
            FROM companies c
            JOIN plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = $1
        """, company_id)

        row = result.first()
        current_queries, reset_date, max_queries = row

        # Reset counter if new month
        if reset_date is None or reset_date < date.today().replace(day=1):
            await self.reset_monthly_usage(company_id)
            current_queries = 0

        if max_queries == -1:  # Unlimited
            return True

        return current_queries < max_queries

    async def increment_document_count(self, company_id: UUID, file_size_bytes: int):
        """Increment document count and storage"""
        await self.db.execute("""
            UPDATE companies
            SET
                usage_documents_count = usage_documents_count + 1,
                usage_storage_bytes = usage_storage_bytes + $2
            WHERE id = $1
        """, company_id, file_size_bytes)

    async def increment_ai_query_count(self, company_id: UUID):
        """Increment AI query count"""
        await self.db.execute("""
            UPDATE companies
            SET usage_ai_queries_count = usage_ai_queries_count + 1
            WHERE id = $1
        """, company_id)

    async def get_usage_stats(self, company_id: UUID) -> dict:
        """Get current usage statistics"""
        result = await self.db.execute("""
            SELECT
                c.usage_documents_count,
                c.usage_storage_bytes,
                c.usage_ai_queries_count,
                c.usage_embeddings_count,
                pl.max_documents,
                pl.max_storage_gb,
                pl.max_ai_queries_per_month
            FROM companies c
            JOIN plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = $1
        """, company_id)

        row = result.first()
        return {
            "documents": {
                "current": row[0],
                "limit": row[4],
                "percentage": (row[0] / row[4] * 100) if row[4] > 0 else 0
            },
            "storage": {
                "current_gb": row[1] / (1024**3),
                "limit_gb": row[5],
                "percentage": (row[1] / (row[5] * 1024**3) * 100) if row[5] > 0 else 0
            },
            "ai_queries": {
                "current": row[2],
                "limit": row[6],
                "percentage": (row[2] / row[6] * 100) if row[6] > 0 else 0
            }
        }
```

### 3. Enforcement in Upload Endpoint

**File:** `backend/app/api/v1/endpoints/documents.py`

```python
from app.services.usage_tracker import UsageTracker

async def _process_document_upload(...):
    # BEFORE processing, check limits
    usage_tracker = UsageTracker(db)

    # Check document count limit
    if not await usage_tracker.check_document_limit(current_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "Document limit reached",
                "message": "Your plan's document limit has been reached. Contact admin to upgrade.",
                "limit_type": "documents"
            }
        )

    # Check storage limit
    file_size = len(await file.read())
    await file.seek(0)  # Reset file pointer

    if not await usage_tracker.check_storage_limit(current_user.company_id, file_size):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "Storage limit reached",
                "message": "Your plan's storage limit has been reached. Delete old documents or contact admin.",
                "limit_type": "storage"
            }
        )

    # ... proceed with upload ...

    # AFTER successful upload, increment usage
    await usage_tracker.increment_document_count(current_user.company_id, file_size)
```

### 4. Enforcement in Chat Endpoint

**File:** `backend/app/api/v1/endpoints/chat.py` (future)

```python
@router.post("/conversations/{conversation_id}/messages")
async def send_message(...):
    usage_tracker = UsageTracker(db)

    # Check AI query limit BEFORE calling Claude API
    if not await usage_tracker.check_ai_query_limit(current_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "AI query limit reached",
                "message": "Your monthly AI query limit has been reached. Resets on the 1st of next month.",
                "limit_type": "ai_queries"
            }
        )

    # ... call Claude API ...

    # Increment after successful response
    await usage_tracker.increment_ai_query_count(current_user.company_id)
```

### 5. Usage Dashboard Endpoint

**File:** `backend/app/api/v1/endpoints/usage.py` (NEW)

```python
from fastapi import APIRouter, Depends
from app.services.usage_tracker import UsageTracker
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/usage")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current usage statistics for the company"""
    usage_tracker = UsageTracker(db)
    stats = await usage_tracker.get_usage_stats(current_user.company_id)

    return {
        "company_id": current_user.company_id,
        "plan_tier": current_user.company.plan_tier,
        "usage": stats,
        "warnings": [
            f"⚠️  {key} usage at {value['percentage']:.0f}%"
            for key, value in stats.items()
            if value['percentage'] > 80
        ]
    }
```

---

## Conservative Limits for Beta (Development Phase)

**Recommended limits to prevent cost overruns:**

### Free Tier (Testing/Dev)
```python
{
    "max_documents": 50,              # ~$3-5 in embeddings
    "max_storage_gb": 1,              # ~$0.02/month S3
    "max_ai_queries_per_month": 100,  # ~$4/month Claude
    "max_document_size_mb": 10,       # Prevent huge PDFs
    "max_users": 1                    # Solo testing
}
# Total cost per company: ~$7-10/month
# 10 beta companies: ~$70-100/month (manageable)
```

### Starter Tier (Small Firms)
```python
{
    "max_documents": 500,             # ~$30-50 in embeddings
    "max_storage_gb": 10,             # ~$0.23/month S3
    "max_ai_queries_per_month": 1000, # ~$40/month Claude
    "max_document_size_mb": 50,
    "max_users": 5
}
# Total cost per company: ~$70-90/month
```

---

## Additional Safeguards

### 1. Rate Limiting (API Level)

**File:** `backend/app/middleware/rate_limiter.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply to expensive endpoints
@router.post("/documents/upload")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def upload_document(...):
    ...

@router.post("/chat/messages")
@limiter.limit("30/minute")  # Max 30 AI queries per minute
async def send_message(...):
    ...
```

### 2. Document Processing Limits

**Prevent processing monster PDFs:**

```python
# In text extraction service
MAX_PAGES_TO_PROCESS = 500  # Skip documents over 500 pages
MAX_CHUNKS_PER_DOCUMENT = 1000  # Prevent creating too many chunks

if page_count > MAX_PAGES_TO_PROCESS:
    raise ValueError(f"Document too large: {page_count} pages (max {MAX_PAGES_TO_PROCESS})")
```

### 3. Embedding Batch Limits

**Prevent runaway embedding generation:**

```python
# In embedding service
MAX_BATCH_SIZE = 100  # Process max 100 chunks at once
DAILY_EMBEDDING_LIMIT = 10000  # Max embeddings per day (company-wide)
```

### 4. Cost Monitoring Alerts

**File:** `backend/app/services/cost_monitor.py`

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CostMonitor:
    """Monitor and alert on cost thresholds"""

    DAILY_COST_ALERT_THRESHOLD = 50.00  # Alert if daily costs exceed $50

    async def log_api_call(self, service: str, tokens: int, cost: float):
        """Log expensive API calls"""
        logger.info(f"API Call: {service} | Tokens: {tokens} | Cost: ${cost:.4f}")

        # TODO: Send alert email if threshold exceeded

    async def estimate_embedding_cost(self, token_count: int) -> float:
        """Estimate OpenAI embedding cost"""
        # text-embedding-3-small: $0.00002 per 1K tokens
        return (token_count / 1000) * 0.00002

    async def estimate_chat_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate Claude API cost"""
        # Claude Sonnet: $3/1M input, $15/1M output
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        return input_cost + output_cost
```

---

## Monitoring Dashboard

### Quick Check Query

```sql
-- See all companies and their usage
SELECT
    c.name,
    c.plan_tier,
    c.usage_documents_count || '/' || pl.max_documents as documents,
    ROUND(c.usage_storage_bytes::numeric / (1024*1024*1024), 2) || 'GB/' || pl.max_storage_gb || 'GB' as storage,
    c.usage_ai_queries_count || '/' || pl.max_ai_queries_per_month as ai_queries,
    CASE
        WHEN c.usage_documents_count::float / pl.max_documents > 0.8 THEN '⚠️ HIGH'
        ELSE '✅ OK'
    END as status
FROM companies c
JOIN plan_limits pl ON pl.plan_tier = c.plan_tier
ORDER BY c.usage_documents_count DESC;
```

---

## Migration Plan

### Step 1: Add Usage Tracking (Immediate)
```bash
cd backend
python -m alembic revision -m "Add usage tracking and limits"
# Edit migration to add columns and plan_limits table
python -m alembic upgrade head
```

### Step 2: Implement UsageTracker Service (Week 1)
- Create `backend/app/services/usage_tracker.py`
- Add unit tests

### Step 3: Add Enforcement (Week 1)
- Update document upload endpoint
- Update chat endpoint (when implemented)
- Add usage endpoint

### Step 4: Add Monitoring (Week 2)
- Implement CostMonitor
- Add logging
- Set up alerts (email when threshold exceeded)

---

## Summary

**Approach:** Hard limits, no payment UI, focus on quality

**Cost Protection:**
- ✅ Database limits per plan tier
- ✅ Usage tracking (documents, storage, AI queries)
- ✅ Hard enforcement (402 Payment Required errors)
- ✅ Rate limiting on expensive endpoints
- ✅ Cost monitoring and alerts

**Beta Budget:** ~$70-100/month for 10 test companies

**When to add payments:** After you have customers willing to pay

---

**Next Step:** Create Alembic migration to add usage tracking schema?
