# app/db/session.py - Simple database session management

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from typing import AsyncGenerator
import logging

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

# Register pgvector type on each new connection
@event.listens_for(engine.sync_engine, "connect")
def register_vector_type(dbapi_conn, connection_record):
    """Register pgvector type on each new database connection."""
    from pgvector.asyncpg import register_vector
    import asyncio

    # Run the async registration synchronously
    try:
        # Create a new event loop for this registration
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(register_vector(dbapi_conn))
            logger.debug("Registered pgvector type on new connection")
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to register pgvector type: {str(e)}", exc_info=True)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            