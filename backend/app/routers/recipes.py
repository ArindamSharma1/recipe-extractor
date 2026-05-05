"""Recipe API endpoints.

All endpoints follow REST conventions and use versioned paths.
Input validation is handled by Pydantic schemas at the boundary.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.recipe import (
    ExtractRequest,
    HealthResponse,
    MealPlanOut,
    MealPlanRequest,
    PaginatedRecipes,
    RecipeListItem,
    RecipeOut,
    ShoppingListOut,
    SubstitutionOut,
    RelatedRecipeOut,
    NutritionOut,
)
from app.services.recipe_service import (
    calculate_total_pages,
    delete_recipe,
    extract_and_store,
    generate_meal_plan,
    get_recipe_by_id,
    list_recipes,
)
from app.services.scraper import ScraperError

logger = logging.getLogger(__name__)

# ── Rate limiter instance ────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1", tags=["recipes"])


# ── Helpers ──────────────────────────────────────────────────────────

def _recipe_to_response(recipe, *, cached: bool = False) -> RecipeOut:
    """Convert an ORM Recipe to the API response schema."""
    return RecipeOut(
        id=recipe.id,
        url=recipe.url,
        title=recipe.title,
        cuisine=recipe.cuisine,
        difficulty=recipe.difficulty,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        total_time=recipe.total_time,
        servings=recipe.servings,
        extraction_confidence=recipe.extraction_confidence,
        created_at=recipe.created_at,
        cached=cached,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        nutrition=(
            NutritionOut.model_validate(recipe.nutrition)
            if recipe.nutrition
            else None
        ),
        substitutions=[
            SubstitutionOut(**s) for s in (recipe.substitutions or [])
        ],
        shopping_list=(
            ShoppingListOut(**recipe.shopping_list)
            if recipe.shopping_list
            else None
        ),
        related_recipes=[
            RelatedRecipeOut(**r) for r in (recipe.related_recipes or [])
        ],
    )


# ── Health Check ─────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse()


# ── Extract Recipe ───────────────────────────────────────────────────

@router.post(
    "/recipes/extract",
    response_model=RecipeOut,
    status_code=status.HTTP_200_OK,
    summary="Extract a recipe from a URL",
)
@limiter.limit("10/minute")
async def extract_recipe(
    request: Request,
    body: ExtractRequest,
    db: AsyncSession = Depends(get_db),
) -> RecipeOut:
    """Scrape a recipe URL, extract data via LLM, and store it.

    If the URL has been processed before, returns the cached result.
    Rate limited to 10 requests per minute per IP.
    """
    url = str(body.url)

    try:
        recipe, cached = await extract_and_store(db, url)
    except ScraperError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during extraction.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during recipe extraction.",
        ) from exc

    return _recipe_to_response(recipe, cached=cached)


# ── List Recipes ─────────────────────────────────────────────────────

@router.get(
    "/recipes/",
    response_model=PaginatedRecipes,
    summary="List all extracted recipes",
)
async def list_all_recipes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRecipes:
    """Return a paginated list of all extracted recipes."""
    recipes, total = await list_recipes(db, page=page, per_page=per_page)
    total_pages = calculate_total_pages(total, per_page)

    return PaginatedRecipes(
        items=[RecipeListItem.model_validate(r) for r in recipes],
        total=total,
        page=page,
        per_page=per_page,
        pages=total_pages,
    )


# ── Get Single Recipe ────────────────────────────────────────────────

@router.get(
    "/recipes/{recipe_id}",
    response_model=RecipeOut,
    summary="Get a recipe by ID",
)
async def get_recipe(
    recipe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RecipeOut:
    """Retrieve a single recipe with all details."""
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )
    return _recipe_to_response(recipe)


# ── Delete Recipe ────────────────────────────────────────────────────

@router.delete(
    "/recipes/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recipe",
)
async def remove_recipe(
    recipe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a recipe and all related data."""
    deleted = await delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )


# ── Meal Plan ────────────────────────────────────────────────────────

@router.post(
    "/recipes/meal-plan",
    response_model=MealPlanOut,
    summary="Generate a merged shopping list from multiple recipes",
)
async def create_meal_plan(
    body: MealPlanRequest,
    db: AsyncSession = Depends(get_db),
) -> MealPlanOut:
    """Combine shopping lists from selected recipes into one deduplicated plan."""
    plan = await generate_meal_plan(db, body.recipe_ids)
    return MealPlanOut(
        recipe_count=plan["recipe_count"],
        recipes=plan["recipes"],
        shopping_list=ShoppingListOut(**plan["shopping_list"]),
    )
