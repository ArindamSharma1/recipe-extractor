"""Async SQLAlchemy engine + session factory.

Supports both Neon PostgreSQL (production) and SQLite (local dev).
The driver is auto-detected from the DATABASE_URL scheme.
"""

from __future__ import annotations

import logging
import re
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


def _build_engine():
    """Create the async engine based on the DATABASE_URL scheme."""
    url = settings.database_url

    if url.startswith("sqlite"):
        # SQLite for local development
        return create_async_engine(url, echo=False)

    # PostgreSQL (Neon) — needs SSL and url cleanup
    ssl_ctx = ssl_module.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl_module.CERT_NONE

    # asyncpg doesn't understand ssl/sslmode as URL params
    clean_url = re.sub(r"[?&]ssl(mode)?=\w+", "", url).rstrip("?")

    return create_async_engine(
        clean_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"ssl": ssl_ctx},
    )


engine = _build_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields a DB session. Commits on success, rolls back on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")
