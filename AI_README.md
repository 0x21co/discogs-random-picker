# Technical System Documentation: Discogs Toolbox

This document is designed for both human developers and AI agents to quickly understand the architecture, logic flow, and extension points of this project.

## 1. System Overview
The **Discogs Toolbox** is a hybrid CLI/Web application designed to manage a user's Discogs record collection. Its core functions include library searching, random selection, and marketplace synchronization (identifying sold items still in the collection).

## 2. Architecture & Design Patterns

### Service-Oriented Architecture (SOA)
The project is built around the `DiscogsService` class located in `app/services/discogs_api.py`.
- **Reasoning:** By decoupling the API logic from the UI (CLI/Web), we ensure consistency and maintainability.
- **Data Persistence:** The system uses a local JSON cache (`.discogs_cache.json`) to minimize API hits and improve performance.

### Flask Application Factory & Blueprints
The web interface follows the Flask Application Factory pattern.
- **`app/__init__.py`**: Entry point for app creation and configuration.
- **Blueprints (`app/routes/`)**: Features are modularized into Blueprints:
    - `picker.py`: Search and random selection logic.
    - `marketplace.py`: Marketplace comparison logic.
- **Frontend**: Server-side rendering with Jinja2 and TailwindCSS (utility-first CSS).

## 3. Core Logic Flow

### Search Logic (`search_library`)
- **Input:** A list of releases and a `query` string.
- **Matching:** 
    - Case-insensitive.
    - If no wildcards (`*`, `?`) are present, it defaults to a substring match (`*query*`).
    - Searches across `Artist`, `Title`, `Label`, `Year`, and `Format`.

### Comparison Logic (`get_sold_comparison`)
- **Process:**
    1. Fetches all collection items and all marketplace orders.
    2. Groups both by `Release ID`.
    3. Compares counts:
        - `Sold Count >= Collection Count` -> Flag as `🔴 SHOULD BE REMOVED`.
        - `Sold Count < Collection Count` -> Flag as `🟡 PARTIAL` (remaining copies exist).

## 4. File Map for AI Agents
- `run.py`: Entry point for the Web server.
- `random_picker.py`: Entry point for the CLI tool.
- `app/services/discogs_api.py`: **Primary Logic Engine.** Start here for core changes.
- `app/routes/`: UI Controllers. Modify these to change how data is presented or to add new pages.
- `app/templates/`: HTML structures.

## 5. Extension Points (How to add features)
1. **New API Feature:** Add a method to `DiscogsService` in `app/services/discogs_api.py`. Ensure it returns a serializable dict or list.
2. **New Web Page:** 
    - Create a new route file in `app/routes/`.
    - Register the Blueprint in `app/__init__.py`.
    - Add a template in `app/templates/`.
3. **Data Analysis:** The `fetch_collection` data is rich. Adding a `stats.py` blueprint for charts (using Chart.js) is a recommended next step.

## 6. Security & Configuration
- **Authentication:** Uses Discogs Personal Access Token via `DISCOGS_TOKEN` environment variable.
- **Environment:** Configuration is managed via `.env` (handled by `python-dotenv`).

## 7. Development Status
- **CLI:** Fully functional.
- **Web:** Fully functional with search, random pick, and marketplace check.
- **Deployment:** Optimized for Debian via Gunicorn/Nginx (see `README_WEB.md`).
