"""Pytest configuration: test database setup, migrations, and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from psycopg import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.seed import seed_all


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a fresh test database, run alembic migrations, and seed data."""
    test_db_name = "care_test"
    admin_conn_str = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/postgres"

    async def _setup():
        # Connect to admin database to recreate test database
        conn = await AsyncConnection.connect(admin_conn_str, autocommit=True)
        try:
            # Terminate active connections to test_db
            await conn.execute(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                  AND pid <> pg_backend_pid();
                """
            )
            await conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
            await conn.execute(f"CREATE DATABASE {test_db_name}")
        finally:
            await conn.close()

    asyncio.run(_setup())

    # Switch settings to test database
    os.environ["DATABASE_URL"] = settings.TEST_DATABASE_URL
    settings.DATABASE_URL = settings.TEST_DATABASE_URL

    # Run alembic upgrade head
    from alembic.config import Config

    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # Seed test database
    asyncio.run(seed_all())

    yield

    # Teardown
    async def _teardown():
        conn = await AsyncConnection.connect(admin_conn_str, autocommit=True)
        try:
            await conn.execute(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                  AND pid <> pg_backend_pid();
                """
            )
            await conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        finally:
            await conn.close()

    try:
        asyncio.run(_teardown())
    except (OSError, RuntimeError) as exc:
        print(f"Warning: teardown failed: {exc}")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a per-test async database session against care_test."""
    test_engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await test_engine.dispose()
