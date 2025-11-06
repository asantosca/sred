# app/db/session.py - Simple database session management

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import asyncpg
from pgvector.asyncpg import register_vector

from app.core.config import settings

async def get_asyncpg_conn():
    """Create asyncpg connection with pgvector support."""
    # Remove the driver portion from the URL for asyncpg
    db_url = settings.DATABASE_URL
    if "+" in db_url:
        db_url = db_url.split("+")[0] + "://" + db_url.split("://")[1]

    conn = await asyncpg.connect(db_url)
    await register_vector(conn)
    return conn

# Create async engine with custom connection factory
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=0,
    pool_pre_ping=True,
    # Use async_creator to register pgvector on each connection
    async_creator=get_asyncpg_conn
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            