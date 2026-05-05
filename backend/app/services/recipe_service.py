"""Recipe business logic layer.

Sits between the API router and the data/LLM layers. Handles
DB lookups, cache detection, and orchestrates scraping → LLM → storage.
"""

from __future__ import annotations

import logging
import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Ingredient, Instruction, NutritionInfo, Recipe
from app.services.llm_service import RecipeGenerationResult, process_recipe
from app.services.scraper import scrape_recipe_url

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 10


# ── Read Operations ──────────────────────────────────────────────────

async def get_recipe_by_url(db: AsyncSession, url: str) -> Recipe | None:
    """Look up a recipe by its source URL (cache check)."""
    stmt = select(Recipe).where(Recipe.url == url)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recipe_by_id(db: AsyncSession, recipe_id: uuid.UUID) -> Recipe | None:
    """Fetch a single recipe with all related data by UUID."""
    stmt = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_recipes(
    db: AsyncSession,
    page: int = 1,
    per_page: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Recipe], int]:
    """Return a paginated list of recipes, newest first.

    Returns:
        Tuple of (recipe list, total count).
    """
    offset = (page - 1) * per_page

    # Count total
    count_stmt = select(func.count()).select_from(Recipe)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Fetch page
    stmt = (
        select(Recipe)
        .order_by(Recipe.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    recipes = list(result.scalars().all())

    return recipes, total


async def delete_recipe(db: AsyncSession, recipe_id: uuid.UUID) -> bool:
    """Delete a recipe and all related data. Returns True if deleted."""
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return False
    await db.delete(recipe)
    await db.flush()
    return True


# ── Write Operations ─────────────────────────────────────────────────

def _build_recipe_from_result(
    url: str,
    result: RecipeGenerationResult,
) -> Recipe:
    """Transform LLM output into a Recipe ORM instance with relations."""
    ext = result.extraction

    recipe = Recipe(
        url=url,
        title=ext.get("title"),
        cuisine=ext.get("cuisine"),
        difficulty=ext.get("difficulty"),
        prep_time=ext.get("prep_time"),
        cook_time=ext.get("cook_time"),
        total_time=ext.get("total_time"),
        servings=ext.get("servings"),
        extraction_confidence=ext.get("extraction_confidence", 0.0),
        substitutions=result.generation.get("substitutions", []),
        shopping_list=result.generation.get("shopping_list", {}),
        related_recipes=result.generation.get("related_recipes", []),
    )

    # Build ingredients
    for ing in ext.get("ingredients", []):
        recipe.ingredients.append(
            Ingredient(
                quantity=ing.get("quantity"),
                unit=ing.get("unit"),
                item=ing.get("item", "unknown"),
            )
        )

    # Build instructions
    instructions_raw = ext.get("instructions", [])
    for idx, text in enumerate(instructions_raw, start=1):
        recipe.instructions.append(
            Instruction(step_number=idx, instruction_text=str(text))
        )

    # Build nutrition
    nutr = result.nutrition
    if nutr:
        recipe.nutrition = NutritionInfo(
            calories=nutr.get("calories"),
            protein=nutr.get("protein"),
            carbs=nutr.get("carbs"),
            fat=nutr.get("fat"),
            fiber=nutr.get("fiber"),
            note=nutr.get("note"),
        )

    return recipe


async def extract_and_store(db: AsyncSession, url: str) -> tuple[Recipe, bool]:
    """Full extraction pipeline: scrape → LLM → store.

    Returns:
        Tuple of (Recipe instance, cached flag).
    """
    # Check cache first
    existing = await get_recipe_by_url(db, url)
    if existing:
        logger.info("Cache hit for %s", url)
        return existing, True

    # Scrape
    scraped_text = await scrape_recipe_url(url)
    logger.info("Scraped %d chars from %s", len(scraped_text), url)

    # LLM pipeline
    result = await process_recipe(scraped_text, url)

    if not result.extraction:
        from app.services.scraper import ScraperError
        raise ScraperError("LLM failed to extract any recipe data.")

    # Build and persist
    recipe = _build_recipe_from_result(url, result)
    db.add(recipe)
    await db.flush()
    await db.refresh(recipe)

    logger.info("Stored recipe '%s' (id=%s)", recipe.title, recipe.id)
    return recipe, False


# ── Meal Plan ────────────────────────────────────────────────────────

async def generate_meal_plan(
    db: AsyncSession,
    recipe_ids: list[uuid.UUID],
) -> dict:
    """Merge shopping lists from multiple recipes into one deduplicated list.

    Returns:
        Dict with recipe_count, recipe names, and merged shopping_list.
    """
    categories = ["produce", "dairy", "meat_seafood", "pantry", "bakery", "other"]
    merged: dict[str, set[str]] = {cat: set() for cat in categories}
    recipe_names: list[str] = []

    for rid in recipe_ids:
        recipe = await get_recipe_by_id(db, rid)
        if not recipe:
            continue

        recipe_names.append(recipe.title or "Untitled")
        shopping = recipe.shopping_list or {}

        for cat in categories:
            items = shopping.get(cat, [])
            if isinstance(items, list):
                merged[cat].update(items)

    # Convert sets to sorted lists
    merged_lists = {cat: sorted(items) for cat, items in merged.items()}

    return {
        "recipe_count": len(recipe_names),
        "recipes": recipe_names,
        "shopping_list": merged_lists,
    }


def calculate_total_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages for pagination."""
    return max(1, math.ceil(total / per_page))
