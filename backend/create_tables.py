"""Standalone script to create all database tables.

Run this once before starting the app:
    python create_tables.py
"""

import asyncio
import sys

# Load env before anything else
from dotenv import load_dotenv
load_dotenv()

from app.database import Base, engine  # noqa: E402
from app.models.recipe import Recipe, Ingredient, Instruction, NutritionInfo  # noqa: E402, F401


async def create_all_tables():
    """Create all tables defined in the ORM models."""
    print("Connecting to database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_all_tables())
    except Exception as e:
        print(f"Failed to create tables: {e}", file=sys.stderr)
        sys.exit(1)
