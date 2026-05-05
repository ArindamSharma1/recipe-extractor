"""Pydantic v2 request / response schemas for the Recipe API.

These schemas handle serialization, validation, and documentation
for all API endpoints. They are intentionally separate from the
SQLAlchemy ORM models to keep concerns decoupled.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ═══════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class ExtractRequest(BaseModel):
    """Payload for the recipe extraction endpoint."""

    url: HttpUrl = Field(..., description="Public recipe URL to scrape and extract.")


class MealPlanRequest(BaseModel):
    """Payload for the meal-plan generation endpoint."""

    recipe_ids: list[uuid.UUID] = Field(
        ...,
        min_length=2,
        description="List of recipe UUIDs to combine into a meal plan.",
    )


# ═══════════════════════════════════════════════════════════════════════
# NESTED RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class IngredientOut(BaseModel):
    """Single ingredient in a recipe response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quantity: str | None = None
    unit: str | None = None
    item: str
    category: str | None = None


class InstructionOut(BaseModel):
    """Single cooking step in a recipe response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    instruction_text: str


class NutritionOut(BaseModel):
    """Estimated per-serving nutrition data."""

    model_config = ConfigDict(from_attributes=True)

    calories: int | None = None
    protein: str | None = None
    carbs: str | None = None
    fat: str | None = None
    fiber: str | None = None
    note: str | None = None


class SubstitutionOut(BaseModel):
    """A single ingredient substitution suggestion."""

    original: str
    substitute: str
    reason: str
    dietary_benefit: str | None = None


class RelatedRecipeOut(BaseModel):
    """A single related recipe suggestion."""

    name: str
    reason: str


class ShoppingListOut(BaseModel):
    """Shopping list grouped by store section."""

    produce: list[str] = Field(default_factory=list)
    dairy: list[str] = Field(default_factory=list)
    meat_seafood: list[str] = Field(default_factory=list)
    pantry: list[str] = Field(default_factory=list)
    bakery: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# MAIN RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class RecipeOut(BaseModel):
    """Full recipe response with all nested data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    title: str | None = None
    cuisine: str | None = None
    difficulty: str | None = None
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    servings: int | None = None
    extraction_confidence: float | None = None
    created_at: datetime
    cached: bool = False

    ingredients: list[IngredientOut] = Field(default_factory=list)
    instructions: list[InstructionOut] = Field(default_factory=list)
    nutrition: NutritionOut | None = None
    substitutions: list[SubstitutionOut] = Field(default_factory=list)
    shopping_list: ShoppingListOut | None = None
    related_recipes: list[RelatedRecipeOut] = Field(default_factory=list)


class RecipeListItem(BaseModel):
    """Compact recipe summary for list / history views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    title: str | None = None
    cuisine: str | None = None
    difficulty: str | None = None
    extraction_confidence: float | None = None
    created_at: datetime


class PaginatedRecipes(BaseModel):
    """Paginated list response."""

    items: list[RecipeListItem]
    total: int
    page: int
    per_page: int
    pages: int


class MealPlanOut(BaseModel):
    """Merged shopping list from multiple recipes."""

    recipe_count: int
    recipes: list[str]
    shopping_list: ShoppingListOut


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
