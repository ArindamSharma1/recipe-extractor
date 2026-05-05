"""Pydantic request/response schemas for the Recipe API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# -- Requests --

class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="Public recipe URL to scrape")


class MealPlanRequest(BaseModel):
    recipe_ids: list[str] = Field(..., min_length=2, description="Recipe IDs to combine")


# -- Nested responses --

class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    quantity: str | None = None
    unit: str | None = None
    item: str
    category: str | None = None


class InstructionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    step_number: int
    instruction_text: str


class NutritionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    calories: int | None = None
    protein: str | None = None
    carbs: str | None = None
    fat: str | None = None
    fiber: str | None = None
    note: str | None = None


class SubstitutionOut(BaseModel):
    original: str
    substitute: str
    reason: str
    dietary_benefit: str | None = None


class RelatedRecipeOut(BaseModel):
    name: str
    reason: str


class ShoppingListOut(BaseModel):
    produce: list[str] = Field(default_factory=list)
    dairy: list[str] = Field(default_factory=list)
    meat_seafood: list[str] = Field(default_factory=list)
    pantry: list[str] = Field(default_factory=list)
    bakery: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


# -- Main responses --

class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
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
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    title: str | None = None
    cuisine: str | None = None
    difficulty: str | None = None
    extraction_confidence: float | None = None
    created_at: datetime


class PaginatedRecipes(BaseModel):
    items: list[RecipeListItem]
    total: int
    page: int
    per_page: int
    pages: int


class MealPlanOut(BaseModel):
    recipe_count: int
    recipes: list[str]
    shopping_list: ShoppingListOut


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
