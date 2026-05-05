"""Recipe extraction prompt template.

Uses chain-of-thought reasoning and anti-hallucination guard-rails
to ensure the LLM only outputs data present in the source text.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

EXTRACTION_SYSTEM = """You are a precise recipe data extraction specialist.
Your job is to extract structured recipe information from raw webpage text.

CRITICAL RULES:
1. Only extract information that is explicitly present in the provided text. Do NOT invent or assume any data.
2. If a field is not found in the text, use null — never guess.
3. For ingredients, always separate quantity, unit, and item name into distinct fields.
4. Think step by step before outputting JSON.
5. After extracting, assign an extraction_confidence score from 0.0 to 1.0 based on how complete the data was in the source text.

You must respond with ONLY a valid JSON object. No markdown, no explanation, no preamble."""

EXTRACTION_HUMAN = """Here is the scraped text from a recipe webpage:

---
{scraped_text}
---

Source URL: {url}

Extract the recipe and return this exact JSON structure:
{{
  "title": "string or null",
  "cuisine": "string or null",
  "prep_time": "string or null",
  "cook_time": "string or null",
  "total_time": "string or null",
  "servings": "integer or null",
  "difficulty": "easy|medium|hard based on number of steps and technique complexity",
  "ingredients": [
    {{"quantity": "string", "unit": "string or null", "item": "string"}}
  ],
  "instructions": ["step 1", "step 2", ...],
  "extraction_confidence": 0.0-1.0
}}

Think step by step: First identify the recipe name. Then find all ingredients with their exact quantities. Then find the instructions in order. Then assess difficulty. Then score your confidence."""

extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", EXTRACTION_SYSTEM),
    ("human", EXTRACTION_HUMAN),
])
