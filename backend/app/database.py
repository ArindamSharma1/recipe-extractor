"""Async SQLAlchemy engine + session factory for Neon PostgreSQL."""

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

# Neon requires SSL. asyncpg needs an actual ssl.SSLContext object,
# not just "ssl=require" in the URL — so we strip the URL param
# and pass the context directly via connect_args.
ssl_context = ssl_module.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl_module.CERT_NONE


def _clean_database_url(url: str) -> str:
    """Remove ssl/sslmode query params from the URL.

    asyncpg doesn't understand these as URL params — SSL must be
    configured via connect_args instead.
    """
    # Strip ?ssl=require or &ssl=require (and sslmode variants)
    import re
    url = re.sub(r"[?&]ssl(mode)?=\w+", "", url)
    # If we stripped the only param, clean up trailing ?
    url = url.rstrip("?")
    return url


engine = create_async_engine(
    _clean_database_url(settings.database_url),
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context},
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields an async DB session. Commits on success, rolls back on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables if they don't exist (runs on startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")
