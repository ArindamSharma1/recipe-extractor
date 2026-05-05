"""Meal plan generation prompt template.

Generates ingredient substitutions, a categorized shopping list,
and related recipe suggestions grounded in the actual recipe.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

GENERATION_SYSTEM = """You are a creative culinary advisor.
Generate practical, useful suggestions grounded in the actual recipe provided.
Do not suggest ingredients not relevant to the dish.
Respond with ONLY valid JSON."""

GENERATION_HUMAN = """For this recipe: {title}
Cuisine: {cuisine}
Ingredients: {ingredients_text}

Generate and return this JSON:
{{
  "substitutions": [
    {{"original": "ingredient", "substitute": "replacement", "reason": "why this works", "dietary_benefit": "e.g. vegan, lower-fat"}}
  ],
  "shopping_list": {{
    "produce": [],
    "dairy": [],
    "meat_seafood": [],
    "pantry": [],
    "bakery": [],
    "other": []
  }},
  "related_recipes": [
    {{"name": "recipe name", "reason": "why it pairs well"}}
  ]
}}

Provide exactly 3 substitutions and exactly 3 related recipes."""

generation_prompt = ChatPromptTemplate.from_messages([
    ("system", GENERATION_SYSTEM),
    ("human", GENERATION_HUMAN),
])
