"""Recipe business logic — sits between the router and data/LLM layers."""

from __future__ import annotations

import logging
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Ingredient, Instruction, NutritionInfo, Recipe
from app.services.llm_service import RecipeGenerationResult, process_recipe
from app.services.scraper import scrape_recipe_url

logger = logging.getLogger(__name__)


async def get_recipe_by_url(db: AsyncSession, url: str) -> Recipe | None:
    result = await db.execute(select(Recipe).where(Recipe.url == url))
    return result.scalar_one_or_none()


async def get_recipe_by_id(db: AsyncSession, recipe_id: str) -> Recipe | None:
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    return result.scalar_one_or_none()


async def list_recipes(db: AsyncSession, page: int = 1, per_page: int = 10) -> tuple[list[Recipe], int]:
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count()).select_from(Recipe))).scalar_one()

    result = await db.execute(
        select(Recipe).order_by(Recipe.created_at.desc()).offset(offset).limit(per_page)
    )
    return list(result.scalars().all()), total


async def delete_recipe(db: AsyncSession, recipe_id: str) -> bool:
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return False
    await db.delete(recipe)
    await db.flush()
    return True


def _build_recipe_from_result(url: str, result: RecipeGenerationResult) -> Recipe:
    """Transform LLM output into a Recipe ORM instance."""
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

    for ing in ext.get("ingredients", []):
        recipe.ingredients.append(Ingredient(
            quantity=ing.get("quantity"),
            unit=ing.get("unit"),
            item=ing.get("item", "unknown"),
        ))

    for idx, text in enumerate(ext.get("instructions", []), start=1):
        recipe.instructions.append(Instruction(step_number=idx, instruction_text=str(text)))

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
    """Full pipeline: check cache → scrape → LLM → store."""
    existing = await get_recipe_by_url(db, url)
    if existing:
        logger.info("Cache hit for %s", url)
        return existing, True

    scraped_text = await scrape_recipe_url(url)
    logger.info("Scraped %d chars from %s", len(scraped_text), url)

    result = await process_recipe(scraped_text, url)

    if not result.extraction:
        from app.services.scraper import ScraperError
        raise ScraperError("LLM couldn't extract any recipe data from this page.")

    recipe = _build_recipe_from_result(url, result)
    db.add(recipe)
    await db.flush()
    await db.refresh(recipe)

    logger.info("Stored recipe '%s' (id=%s)", recipe.title, recipe.id)
    return recipe, False


async def generate_meal_plan(db: AsyncSession, recipe_ids: list[str]) -> dict:
    """Merge shopping lists from multiple recipes, deduplicating items."""
    categories = ["produce", "dairy", "meat_seafood", "pantry", "bakery", "other"]
    merged: dict[str, set[str]] = {cat: set() for cat in categories}
    recipe_names: list[str] = []

    for rid in recipe_ids:
        recipe = await get_recipe_by_id(db, rid)
        if not recipe:
            continue
        recipe_names.append(recipe.title or "Untitled")
        for cat in categories:
            items = (recipe.shopping_list or {}).get(cat, [])
            if isinstance(items, list):
                merged[cat].update(items)

    return {
        "recipe_count": len(recipe_names),
        "recipes": recipe_names,
        "shopping_list": {cat: sorted(items) for cat, items in merged.items()},
    }


def calculate_total_pages(total: int, per_page: int) -> int:
    return max(1, math.ceil(total / per_page))
