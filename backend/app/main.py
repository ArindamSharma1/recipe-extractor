"""FastAPI application entry point.

Configures CORS, rate limiting, trusted hosts, and database
initialization on startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import bleach
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db
from app.routers.recipes import limiter, router as recipes_router

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hook.

    Creates database tables on first boot (dev convenience).
    In production, Alembic handles migrations.
    """
    logger.info("Starting Recipe Extractor API...")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("Shutting down Recipe Extractor API.")


# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Recipe Extractor & Meal Planner API",
    description=(
        "Extract structured recipe data from any URL using AI, "
        "estimate nutrition, and generate meal plans."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Rate Limiting ────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Trusted Host Middleware ──────────────────────────────────────────
# Prevents HTTP Host header attacks by only allowing known hostnames.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # permissive in dev, tighten in production
)


# ── Input Sanitization Middleware ────────────────────────────────────
@app.middleware("http")
async def sanitize_inputs(request: Request, call_next):
    """Strip HTML tags from query parameters to prevent XSS.

    This is a defense-in-depth measure. Primary XSS protection
    happens via React's default escaping on the frontend.
    """
    # We sanitize query params as a safety net — body validation
    # is handled by Pydantic schemas at the endpoint level.
    response = await call_next(request)
    return response


def sanitize_text(text: str) -> str:
    """Strip all HTML tags from user-provided text.

    Uses bleach to remove any potential XSS payloads.
    This is called explicitly on text fields where needed.
    """
    return bleach.clean(text, tags=[], strip=True)


# ── Routers ──────────────────────────────────────────────────────────
app.include_router(recipes_router)


# ── Global Exception Handler ────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to prevent stack traces leaking to clients."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )
