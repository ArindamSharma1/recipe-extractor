# Recipe Extractor & Meal Planner

Paste a recipe URL, get back structured data — ingredients, steps, nutrition, substitutions, shopping list. All extracted by AI.

Built with FastAPI, LangChain (Gemini), React, and PostgreSQL (Neon).

---

## Setup

**Step 1:** Copy `.env.example` to `.env` inside the `backend/` folder and fill in your `GEMINI_API_KEY` and `DATABASE_URL`

```bash
cp backend/.env.example backend/.env
# open backend/.env and put your actual values
```

**Step 2:** Create the database tables

```bash
cd backend
pip install -r requirements.txt
python create_tables.py
cd ..
```

**Step 3:** Start everything

```bash
bash start.sh
```

That's it — open http://localhost:5173

---

## What it does

- **Extract tab** — Paste any recipe URL. The app scrapes it, sends the text to Gemini, and pulls out the recipe in a clean format. You get ingredients (with quantities separated), step-by-step instructions, difficulty rating, and a confidence score showing how much data it found.

- **History tab** — All your extracted recipes in a table. You can view details, delete entries, or select multiple recipes to generate a combined shopping list (the meal plan feature).

- **Nutrition** — Each recipe gets a per-serving nutrition estimate based on the actual ingredients.

- **Substitutions** — AI suggests 3 ingredient swaps with reasons (like "use coconut oil instead of butter for dairy-free").

- **Shopping list** — Ingredients sorted by store section (produce, dairy, pantry, etc).

---

## API Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| `POST` | `/api/v1/recipes/extract` | Send a URL, get back the full recipe |
| `GET` | `/api/v1/recipes/` | List all recipes (paginated) |
| `GET` | `/api/v1/recipes/{id}` | Get one recipe with all details |
| `DELETE` | `/api/v1/recipes/{id}` | Delete a recipe |
| `POST` | `/api/v1/recipes/meal-plan` | Send recipe IDs, get merged shopping list |
| `GET` | `/api/v1/health` | Health check |

The extract endpoint is rate limited to 10 requests per minute per IP.

If you extract the same URL twice, it returns the cached result instead of hitting the LLM again.

### Example request

```bash
curl -X POST http://localhost:8000/api/v1/recipes/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/"}'
```

---

## How it works

```
URL → Scraper → Gemini (3 calls) → PostgreSQL → API response
```

1. You submit a URL
2. The scraper fetches the page and strips out scripts, nav, footer — keeps just the text
3. Three separate LLM calls run:
   - Recipe extraction (title, ingredients, steps)
   - Nutrition estimation
   - Substitutions + shopping list + related recipes
4. Everything gets saved to the database
5. Next time someone submits the same URL, it skips the LLM and returns the saved version

Each LLM call is independent. If nutrition estimation fails, you still get the recipe and substitutions.

---

## Project structure

```
recipe-extractor/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, rate limiting
│   │   ├── config.py        # Settings from .env
│   │   ├── database.py      # Async SQLAlchemy + Neon SSL
│   │   ├── models/          # ORM models (Recipe, Ingredient, etc)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Scraper, LLM calls, business logic
│   │   └── prompts/         # LangChain prompt templates
│   ├── create_tables.py     # Run once to set up the DB
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/       # RecipeExtractor, RecipeHistory, etc
│       ├── hooks/            # useRecipes.js
│       └── api/              # Axios client
├── start.sh
└── README.md
```

---

## Security stuff

Not just a homework project — these are real security measures:

- **SSRF protection** — The scraper blocks requests to private IPs (127.x, 10.x, 192.168.x, 169.254.x). Without this, someone could submit `http://169.254.169.254/` and read cloud metadata.

- **Content capping** — Scraped text is cut at 50,000 chars before going to the LLM. This limits prompt injection from malicious pages.

- **No raw SQL anywhere** — Everything uses SQLAlchemy ORM, so queries are parameterized by default. SQL injection isn't possible.

- **Rate limiting** — 10 requests/minute on the extract endpoint via slowapi.

- **UUID primary keys** — Recipe IDs are UUIDs, not auto-incrementing integers. Harder to guess or enumerate.

- **Input validation** — Pydantic validates every request body. Invalid data gets rejected before it touches the database.

---

## Prompt design

The LLM prompts are in `backend/app/prompts/`. Some decisions worth noting:

- **Three separate calls instead of one big call.** More reliable. If nutrition parsing fails, the recipe extraction still works.

- **Chain-of-thought.** The extraction prompt tells the LLM to think step by step before outputting JSON. This helps with complex recipes.

- **Anti-hallucination rules.** Every prompt says "if you can't find it, use null — don't guess." The LLM also self-reports a confidence score.

- **Low temperature (0.3).** We want factual extraction, not creative writing. Higher temps make ingredient quantities drift.

---

## Environment variables

| Variable | What it is |
|----------|-----------|
| `DATABASE_URL` | Neon PostgreSQL connection string (must include `?ssl=require`) |
| `GEMINI_API_KEY` | Google Gemini API key from [AI Studio](https://aistudio.google.com/apikey) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (default: `http://localhost:5173`) |

---

## Test URLs

These work well for testing:

```
https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/
https://www.simplyrecipes.com/recipes/homemade_pizza/
https://www.bbcgoodfood.com/recipes/chicken-tikka-masala
```
