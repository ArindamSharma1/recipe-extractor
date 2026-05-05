"""Nutrition estimation prompt template.

Instructs the LLM to act as a registered dietitian and estimate
per-serving macronutrients based solely on the ingredient list.
Includes a mandatory disclaimer note in the output.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

NUTRITION_SYSTEM = """You are a registered dietitian estimating nutritional content.
Base estimates ONLY on the provided ingredients and quantities.
Always note that these are estimates.
Respond with ONLY valid JSON. No markdown."""

NUTRITION_HUMAN = """Estimate nutrition per serving for this recipe:

Recipe: {title}
Servings: {servings}
Ingredients:
{ingredients_text}

Return:
{{
  "calories": integer,
  "protein": "Xg",
  "carbs": "Xg",
  "fat": "Xg",
  "fiber": "Xg",
  "note": "brief disclaimer about estimate accuracy"
}}"""

nutrition_prompt = ChatPromptTemplate.from_messages([
    ("system", NUTRITION_SYSTEM),
    ("human", NUTRITION_HUMAN),
])
