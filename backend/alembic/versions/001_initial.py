"""Initial migration — create all tables.

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create recipes, ingredients, instructions, and nutrition_info tables."""
    # Recipes
    op.create_table(
        "recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(2048), unique=True, index=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("cuisine", sa.String(100), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=True),
        sa.Column("prep_time", sa.String(50), nullable=True),
        sa.Column("cook_time", sa.String(50), nullable=True),
        sa.Column("total_time", sa.String(50), nullable=True),
        sa.Column("servings", sa.Integer, nullable=True),
        sa.Column("extraction_confidence", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("substitutions", postgresql.JSONB, nullable=True),
        sa.Column("shopping_list", postgresql.JSONB, nullable=True),
        sa.Column("related_recipes", postgresql.JSONB, nullable=True),
    )

    # Ingredients
    op.create_table(
        "ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.String(50), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("item", sa.String(300), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
    )

    # Instructions
    op.create_table(
        "instructions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("instruction_text", sa.Text, nullable=False),
    )

    # Nutrition Info
    op.create_table(
        "nutrition_info",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recipes.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("calories", sa.Integer, nullable=True),
        sa.Column("protein", sa.String(30), nullable=True),
        sa.Column("carbs", sa.String(30), nullable=True),
        sa.Column("fat", sa.String(30), nullable=True),
        sa.Column("fiber", sa.String(30), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("nutrition_info")
    op.drop_table("instructions")
    op.drop_table("ingredients")
    op.drop_table("recipes")
