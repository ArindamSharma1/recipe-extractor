"""Async SQLAlchemy engine and session factory.

Uses asyncpg as the driver for fully asynchronous database access.
All database interactions go through the ORM — no raw SQL — which
prevents SQL injection by default via parameterized queries.

The DATABASE_URL must include ?ssl=require for Neon cloud PostgreSQL.
"""

from __future__ import annotations

import logging
import ssl as ssl_module
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# ── SSL context for Neon cloud PostgreSQL ────────────────────────────
# Neon requires SSL connections. We create a permissive SSL context
# so asyncpg can connect without needing local CA certificates.
ssl_context = ssl_module.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl_module.CERT_NONE

# ── Engine ────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context},
)

# ── Session factory ──────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative base ────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── Dependency ──────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session.

    Automatically commits on success and rolls back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables if they don't exist.

    Called on app startup. Uses the ORM metadata to generate
    CREATE TABLE IF NOT EXISTS statements.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")
