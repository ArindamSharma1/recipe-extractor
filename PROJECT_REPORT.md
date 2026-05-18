# Recipe Extractor & Meal Planner - Project Report

## 1. Project Overview
The "Recipe Extractor & Meal Planner" is a full-stack web application designed to simplify the cooking and meal-planning experience. By taking the URL of a recipe online, the system leverages Artificial Intelligence (Google Gemini) to read the page, strip away the non-essential content (ads, long stories), and extract clean, structured recipe data. 

### Key Features
- **URL-Based Extraction**: Scrapes web pages and extracts the title, ingredients (quantities and units separated), and step-by-step instructions.
- **Nutrition Estimation**: Automatically estimates per-serving nutrition based on the extracted ingredients.
- **Intelligent Substitutions**: AI suggests ingredient swaps along with reasoning (e.g., dairy-free alternatives).
- **History & Caching**: All extracted recipes are saved to a PostgreSQL database. Repeated URLs skip the scraping and LLM steps and load instantly from the cache.
- **Meal Planning & Shopping List**: Users can select multiple recipes from their history to generate a unified shopping list categorized by store section.

---

## 2. Technology Stack

### Backend
- **Framework**: FastAPI (Python) - chosen for its high performance and native async support.
- **Database**: PostgreSQL (hosted on Neon) managed with async SQLAlchemy and `asyncpg`. Alembic is used for migrations.
- **AI/LLM**: LangChain integrated with Google Gemini (`langchain-google-genai`).
- **Web Scraping**: `httpx`, `beautifulsoup4`, and `lxml` for fast, reliable HTML fetching and parsing.
- **Rate Limiting**: `slowapi` to protect API endpoints.

### Frontend
- **Framework**: React.js built with Vite.
- **Styling**: Tailwind CSS for a responsive, modern, and highly customized UI.
- **Icons**: Lucide React.
- **HTTP Client**: Axios.

---

## 3. Architecture & Implementation Details

### 3.1. Data Flow Pipeline
1. **User Input**: A user submits a URL on the frontend application.
2. **Scraping Phase**: The backend receives the URL. The scraper fetches the raw HTML and removes `script`, `style`, `nav`, `header`, and `footer` tags to isolate the core article text.
3. **LLM Processing (Gemini)**: The system makes three *independent* and concurrent LLM calls using LangChain:
   - **Recipe Extraction**: Extracts title, ingredients (with units/amounts), instructions, and difficulty.
   - **Nutrition Estimation**: Calculates calories, protein, carbs, etc.
   - **Substitutions & Context**: Identifies 3 practical substitutions, generates a categorized shopping list, and suggests related recipe types.
4. **Storage**: The parsed data is validated using Pydantic schemas and persisted to the PostgreSQL database using SQLAlchemy ORM.
5. **Response**: The structured JSON data is returned to the React frontend to be displayed.

### 3.2. Backend Logic & Security Measures
The backend (`app/main.py`) is designed with robustness and real-world security in mind:
- **SSRF (Server-Side Request Forgery) Protection**: The web scraper explicitly blocks requests to private IP ranges (e.g., `127.0.0.1`, `169.254.x.x`). This prevents malicious users from tricking the server into accessing internal cloud metadata.
- **Content Capping**: Scraped text is truncated at 50,000 characters before being sent to the LLM. This manages token limits and mitigates prompt injection attacks from malicious web pages.
- **SQL Injection Prevention**: Entirely avoids raw SQL strings; all database interactions use SQLAlchemy ORM.
- **Rate Limiting**: The `/extract` endpoint is limited to 10 requests per minute per IP via `slowapi` to prevent abuse.
- **Sanitization**: Uses `bleach` to strip out HTML tags from user inputs, serving as a defense-in-depth measure against XSS.
- **UUID Primary Keys**: Recipe IDs are UUIDs rather than auto-incrementing integers, making it much harder to guess or enumerate records.

### 3.3. LLM Prompt Design
The LangChain prompts (`backend/app/prompts/`) are rigorously engineered to ensure accuracy:
- **Chain-of-Thought**: The LLM is instructed to "think step by step" before outputting the final JSON, significantly improving extraction accuracy for complex or poorly formatted recipes.
- **Anti-Hallucination Guidelines**: Prompts contain specific instructions to output `null` if a piece of information is missing, rather than guessing. The LLM also self-reports a "confidence score".
- **Low Temperature**: Model temperature is set low (0.3) to ensure factual, deterministic extraction rather than creative generation.
- **Modularity**: By splitting tasks into three separate LLM calls, the app ensures that a failure in one area (e.g., nutrition parsing) doesn't crash the entire recipe extraction process.

### 3.4. Frontend Implementation
The React application (`frontend/src/`) focuses on a seamless and premium User Experience:
- **State Management**: Uses React Hooks (`useState`, and custom hooks) to manage application state between tabs (Extract vs. History).
- **Design Aesthetic**: Features a dark-mode-first design (`bg-slate-950`) with an ambient background glow, glassmorphism (`backdrop-blur-xl`), and vibrant gradients to provide a premium feel.
- **Component Architecture**: Clean separation into modular components like `RecipeExtractor` and `RecipeHistory` for maintainability.

---

## 4. API Endpoints
The RESTful API provides the following core endpoints:
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/recipes/extract` | Primary endpoint. Takes a URL, runs the scraper & LLM pipeline, and returns full recipe data. |
| `GET` | `/api/v1/recipes/` | Retrieves a paginated list of previously extracted recipes from the database. |
| `GET` | `/api/v1/recipes/{id}` | Fetches a single detailed recipe by its UUID. |
| `DELETE` | `/api/v1/recipes/{id}` | Deletes a recipe from the database. |
| `POST` | `/api/v1/recipes/meal-plan` | Accepts an array of recipe IDs and returns a consolidated, categorized shopping list. |
| `GET` | `/api/v1/health` | Health check endpoint to verify API status. |

---

## 5. Summary
The **Recipe Extractor & Meal Planner** is a highly capable full-stack application that seamlessly blends standard web development practices with modern AI capabilities. By implementing robust security measures (SSRF protection, content capping), a scalable architecture (FastAPI, modular LLM calls), and an aesthetically pleasing React frontend, it serves as a highly practical, production-ready tool.
