"""SQLAlchemy ORM models for the Recipe Extractor.

SECURITY NOTE — SQL Injection Prevention:
All database interactions use the SQLAlchemy ORM exclusively.
No raw SQL strings are constructed anywhere in this codebase.
The ORM generates parameterized queries automatically, which
makes SQL injection attacks structurally impossible.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ── Helper ───────────────────────────────────────────────────────────
def _utcnow() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    """Generate a new UUID4 for primary keys."""
    return uuid.uuid4()


# ── Recipe ───────────────────────────────────────────────────────────
class Recipe(Base):
    """Core recipe entity extracted from a URL.

    Uses UUID primary keys instead of auto-incrementing integers
    to prevent enumeration attacks on the API.
    """

    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=True)
    cuisine = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=True)
    prep_time = Column(String(50), nullable=True)
    cook_time = Column(String(50), nullable=True)
    total_time = Column(String(50), nullable=True)
    servings = Column(Integer, nullable=True)
    extraction_confidence = Column(Float, nullable=True, default=0.0)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # JSONB columns for flexible nested data
    substitutions = Column(JSONB, nullable=True, default=list)
    shopping_list = Column(JSONB, nullable=True, default=dict)
    related_recipes = Column(JSONB, nullable=True, default=list)

    # Relationships
    ingredients = relationship(
        "Ingredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    instructions = relationship(
        "Instruction",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Instruction.step_number",
    )
    nutrition = relationship(
        "NutritionInfo",
        back_populates="recipe",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


# ── Ingredient ───────────────────────────────────────────────────────
class Ingredient(Base):
    """Single ingredient line belonging to a recipe."""

    __tablename__ = "ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    item = Column(String(300), nullable=False)
    category = Column(String(100), nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")


# ── Instruction ──────────────────────────────────────────────────────
class Instruction(Base):
    """Ordered cooking step belonging to a recipe."""

    __tablename__ = "instructions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number = Column(Integer, nullable=False)
    instruction_text = Column(Text, nullable=False)

    recipe = relationship("Recipe", back_populates="instructions")


# ── Nutrition Info ───────────────────────────────────────────────────
class NutritionInfo(Base):
    """Estimated per-serving nutrition for a recipe (one-to-one)."""

    __tablename__ = "nutrition_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    calories = Column(Integer, nullable=True)
    protein = Column(String(30), nullable=True)
    carbs = Column(String(30), nullable=True)
    fat = Column(String(30), nullable=True)
    fiber = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)

    recipe = relationship("Recipe", back_populates="nutrition")
