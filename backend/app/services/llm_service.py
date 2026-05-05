"""LangChain + Google Gemini LLM service.

Orchestrates three separate LLM calls for recipe extraction,
nutrition estimation, and meal-plan generation. Each call is
isolated for reliability — a failure in nutrition estimation
won't block the recipe extraction result.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.prompts.extraction import extraction_prompt
from app.prompts.meal_plan import generation_prompt
from app.prompts.nutrition import nutrition_prompt

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"
TEMPERATURE = 0.3          # Low temperature for factual extraction
MAX_OUTPUT_TOKENS = 4096


# ── Result container ─────────────────────────────────────────────────
@dataclass
class RecipeGenerationResult:
    """Aggregated result from all three LLM calls."""

    extraction: dict = field(default_factory=dict)
    nutrition: dict = field(default_factory=dict)
    generation: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class LLMServiceError(Exception):
    """Raised when an LLM call fails irrecoverably."""


# ── JSON Parsing ─────────────────────────────────────────────────────

def _clean_json_response(text: str) -> str:
    """Strip markdown fences and whitespace from LLM JSON output.

    LLMs frequently wrap JSON in ```json ... ``` despite explicit
    instructions not to. This normalises the response.
    """
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_json(text: str, context: str) -> dict:
    """Safely parse JSON from an LLM response.

    Args:
        text: Raw LLM output string.
        context: Description of which call produced this (for logging).

    Returns:
        Parsed dict.

    Raises:
        LLMServiceError: If JSON parsing fails.
    """
    cleaned = _clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse JSON from %s call: %s\nRaw output:\n%s",
            context,
            exc,
            cleaned[:500],
        )
        raise LLMServiceError(
            f"LLM returned invalid JSON for {context}: {exc}"
        ) from exc


# ── LLM Client ───────────────────────────────────────────────────────

def _get_llm() -> ChatGoogleGenerativeAI:
    """Create a configured Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=settings.gemini_api_key,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


# ── Individual LLM Calls ─────────────────────────────────────────────

async def _extract_recipe(llm: ChatGoogleGenerativeAI, scraped_text: str, url: str) -> dict:
    """Run the recipe extraction prompt against the LLM.

    Returns:
        Parsed extraction dict with recipe fields.
    """
    chain = extraction_prompt | llm
    response = await chain.ainvoke({
        "scraped_text": scraped_text,
        "url": url,
    })
    return _parse_json(response.content, "extraction")


async def _estimate_nutrition(
    llm: ChatGoogleGenerativeAI,
    title: str,
    servings: int | None,
    ingredients_text: str,
) -> dict:
    """Run the nutrition estimation prompt against the LLM.

    Returns:
        Parsed nutrition dict with macros.
    """
    chain = nutrition_prompt | llm
    response = await chain.ainvoke({
        "title": title or "Unknown Recipe",
        "servings": servings or 1,
        "ingredients_text": ingredients_text,
    })
    return _parse_json(response.content, "nutrition")


async def _generate_extras(
    llm: ChatGoogleGenerativeAI,
    title: str,
    cuisine: str | None,
    ingredients_text: str,
) -> dict:
    """Run the generation prompt for substitutions, shopping list, etc.

    Returns:
        Parsed generation dict with substitutions, shopping_list, related_recipes.
    """
    chain = generation_prompt | llm
    response = await chain.ainvoke({
        "title": title or "Unknown Recipe",
        "cuisine": cuisine or "Unknown",
        "ingredients_text": ingredients_text,
    })
    return _parse_json(response.content, "generation")


# ── Ingredient Formatting ───────────────────────────────────────────

def _format_ingredients(ingredients: list[dict]) -> str:
    """Format an ingredient list into a readable text block for prompts."""
    lines = []
    for ing in ingredients:
        qty = ing.get("quantity", "")
        unit = ing.get("unit", "")
        item = ing.get("item", "unknown")
        line = f"- {qty} {unit} {item}".strip()
        lines.append(line)
    return "\n".join(lines) if lines else "No ingredients found."


# ── Public API ───────────────────────────────────────────────────────

async def process_recipe(scraped_text: str, url: str) -> RecipeGenerationResult:
    """Run the full LLM pipeline: extract → nutrition → extras.

    Each step is independent — a failure in one step is captured in
    the result's `errors` list without blocking the others.

    Args:
        scraped_text: Cleaned text from the web scraper.
        url: Original recipe URL.

    Returns:
        RecipeGenerationResult with data from all three steps.
    """
    result = RecipeGenerationResult()
    llm = _get_llm()

    # Step 1 — Recipe extraction (required)
    try:
        result.extraction = await _extract_recipe(llm, scraped_text, url)
        logger.info("Recipe extraction succeeded for %s", url)
    except (LLMServiceError, Exception) as exc:
        logger.error("Recipe extraction failed: %s", exc)
        result.errors.append(f"Extraction failed: {exc}")
        return result  # Can't proceed without the base extraction

    # Build ingredients text for downstream calls
    ingredients = result.extraction.get("ingredients", [])
    ingredients_text = _format_ingredients(ingredients)
    title = result.extraction.get("title")
    servings = result.extraction.get("servings")
    cuisine = result.extraction.get("cuisine")

    # Step 2 — Nutrition estimation (optional, best-effort)
    try:
        result.nutrition = await _estimate_nutrition(
            llm, title, servings, ingredients_text
        )
        logger.info("Nutrition estimation succeeded.")
    except (LLMServiceError, Exception) as exc:
        logger.warning("Nutrition estimation failed (non-fatal): %s", exc)
        result.errors.append(f"Nutrition estimation failed: {exc}")

    # Step 3 — Extras generation (optional, best-effort)
    try:
        result.generation = await _generate_extras(
            llm, title, cuisine, ingredients_text
        )
        logger.info("Extras generation succeeded.")
    except (LLMServiceError, Exception) as exc:
        logger.warning("Extras generation failed (non-fatal): %s", exc)
        result.errors.append(f"Extras generation failed: {exc}")

    return result
