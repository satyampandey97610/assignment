"""Database connections, session management, and connection pooling."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def reset_db_engine(db_url: str | None = None) -> None:
    """Rebind global engine and sessionmaker (used by test fixtures)."""
    global engine, AsyncSessionLocal
    target_url = db_url or settings.DATABASE_URL
    engine = create_async_engine(target_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_connection_pool(db_url: str | None = None) -> AsyncConnectionPool:
    """Create an AsyncConnectionPool for psycopg3/checkpointer with dict_row & autocommit."""
    conn_str = (db_url or settings.DATABASE_URL).replace("postgresql+psycopg://", "postgresql://")
    return AsyncConnectionPool(
        conninfo=conn_str,
        max_size=20,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession with statement_timeout set."""
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL statement_timeout = {settings.DB_STATEMENT_TIMEOUT_MS}")
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
