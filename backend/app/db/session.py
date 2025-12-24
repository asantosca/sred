# app/db/session.py - Simple database session management

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, pool
from typing import AsyncGenerator
import logging
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=0,
    pool_pre_ping=True,
)

# Note: pgvector registration is handled by vector_storage_service
# when it creates its own asyncpg connection pool for vector operations.
# We don't need to register it here for SQLAlchemy connections since
# those don't handle vector types directly.

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models with bc_legal_ds schema
Base = declarative_base()
Base.metadata.schema = 'bc_legal_ds'

from fastapi import Request
from sqlalchemy import text
from app.core.tenant import get_tenant_context

async def get_db(request: Request = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with RLS context set if authenticated.
    
    This dependency yields a session that has the `app.current_company_id` 
    variable set for Row-Level Security (RLS) enforcement.
    """
    async with async_session_factory() as session:
        try:
            # Enforce Row-Level Security (RLS)
            if request:
                company_id = None
                
                # 1. Try to get from request state (set by middleware)
                if hasattr(request.state, "company_id"):
                    company_id = request.state.company_id
                
                # 2. Fallback: Extract directly if middleware didn't run
                if not company_id:
                    try:
                        # We use a local import if needed, but top-level is fine 
                        # as long as app.core.tenant doesn't import get_db
                        ctx = await get_tenant_context(request)
                        if ctx:
                            company_id = ctx.company_id
                    except Exception:
                        pass
                
                # 3. Set the RLS variable in the database session
                if company_id:
                    await session.execute(
                        text("SELECT set_config('app.current_company_id', :cid, true)"),
                        {"cid": str(company_id)}
                    )

            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

            