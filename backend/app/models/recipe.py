"""SQLAlchemy ORM models.

All database access goes through these models — no raw SQL anywhere.
This means queries are parameterized automatically, preventing SQL injection.

Uses UUIDs stored as strings for cross-database compatibility (works on
both PostgreSQL and SQLite).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Recipe(Base):
    """Core recipe entity. Uses string UUIDs to prevent ID enumeration."""

    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=True)
    cuisine = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=True)
    prep_time = Column(String(50), nullable=True)
    cook_time = Column(String(50), nullable=True)
    total_time = Column(String(50), nullable=True)
    servings = Column(Integer, nullable=True)
    extraction_confidence = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    # JSON columns for nested data (works on both PG and SQLite)
    substitutions = Column(JSON, nullable=True, default=list)
    shopping_list = Column(JSON, nullable=True, default=dict)
    related_recipes = Column(JSON, nullable=True, default=list)

    ingredients = relationship(
        "Ingredient", back_populates="recipe",
        cascade="all, delete-orphan", lazy="selectin",
    )
    instructions = relationship(
        "Instruction", back_populates="recipe",
        cascade="all, delete-orphan", lazy="selectin",
        order_by="Instruction.step_number",
    )
    nutrition = relationship(
        "NutritionInfo", back_populates="recipe",
        cascade="all, delete-orphan", uselist=False, lazy="selectin",
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    item = Column(String(300), nullable=False)
    category = Column(String(100), nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")


class Instruction(Base):
    __tablename__ = "instructions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    instruction_text = Column(Text, nullable=False)

    recipe = relationship("Recipe", back_populates="instructions")


class NutritionInfo(Base):
    __tablename__ = "nutrition_info"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), unique=True, nullable=False)
    calories = Column(Integer, nullable=True)
    protein = Column(String(30), nullable=True)
    carbs = Column(String(30), nullable=True)
    fat = Column(String(30), nullable=True)
    fiber = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)

    recipe = relationship("Recipe", back_populates="nutrition")
