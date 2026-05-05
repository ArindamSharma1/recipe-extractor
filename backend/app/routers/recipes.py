"""Recipe API endpoints."""

import logging

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
    NutritionOut,
    PaginatedRecipes,
    RecipeListItem,
    RecipeOut,
    RelatedRecipeOut,
    ShoppingListOut,
    SubstitutionOut,
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

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1", tags=["recipes"])


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
            if recipe.nutrition else None
        ),
        substitutions=[
            SubstitutionOut(**s) for s in (recipe.substitutions or [])
        ],
        shopping_list=(
            ShoppingListOut(**recipe.shopping_list)
            if recipe.shopping_list else None
        ),
        related_recipes=[
            RelatedRecipeOut(**r) for r in (recipe.related_recipes or [])
        ],
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()


@router.post("/recipes/extract", response_model=RecipeOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def extract_recipe(
    request: Request,
    body: ExtractRequest,
    db: AsyncSession = Depends(get_db),
) -> RecipeOut:
    """Scrape a URL, extract via LLM, store it. Returns cached result if URL was seen before."""
    url = str(body.url)
    try:
        recipe, cached = await extract_and_store(db, url)
    except ScraperError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Extraction failed for %s", url)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Recipe extraction failed.") from exc

    return _recipe_to_response(recipe, cached=cached)


@router.get("/recipes/", response_model=PaginatedRecipes)
async def list_all_recipes(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRecipes:
    recipes, total = await list_recipes(db, page=page, per_page=per_page)
    return PaginatedRecipes(
        items=[RecipeListItem.model_validate(r) for r in recipes],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_total_pages(total, per_page),
    )


@router.get("/recipes/{recipe_id}", response_model=RecipeOut)
async def get_recipe(recipe_id: str, db: AsyncSession = Depends(get_db)) -> RecipeOut:
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    return _recipe_to_response(recipe)


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipe(recipe_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")


@router.post("/recipes/meal-plan", response_model=MealPlanOut)
async def create_meal_plan(body: MealPlanRequest, db: AsyncSession = Depends(get_db)) -> MealPlanOut:
    """Combine shopping lists from selected recipes into one list."""
    plan = await generate_meal_plan(db, body.recipe_ids)
    return MealPlanOut(
        recipe_count=plan["recipe_count"],
        recipes=plan["recipes"],
        shopping_list=ShoppingListOut(**plan["shopping_list"]),
    )
