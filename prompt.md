### Prompt for New Conversation: "CACC Dog Bot - Comprehensive Project Context"

**Context & Goal:**
I am building `cacc_dogs`, a Python-based static site generator that scrapes, tracks, and visualizes dog adoption data from Chicago Animal Care & Control (CACC). My goal is to provide a high-performance, user-friendly dashboard for volunteers.

**Technical Stack:**
* **Language:** Python 3.12
* **Scraper:**
    * **Phase 1 (Discovery):** **Playwright (Crawlee)** with **Stealth Mode** (Fingerprint generation) for robust ID collection, replacing SeleniumBase.
    * **Phase 2 (Details):** `aiohttp` for high-speed async data fetching of animal details (cookies inherited from Phase 1).
    * **Phase 3 (Enrichment):** **Crawlee + Playwright** using an **Embed Proxy Strategy** to bypass Facebook login walls and aggregate multiple media links.
* **Data Persistence:** **Hybrid DuckDB + CSV**. Uses DuckDB for high-performance in-memory SQL merging (`UPSERT` logic) and distinct record processing, while outputting optimized CSVs (`dogs_active.csv`, `dogs_historic.csv`) for the frontend.
* **Visualization:**
    * **Interactive:** `Chart.js` for all client-side charts (Trends, Rescues, Population).
    * **Mapping:** Leaflet.js with client-side clustering and spatial indexing.
* **Frontend:** Jinja2 templating with a **Global CSS Variable Design System**. Features a responsive "Frosted Glass" sticky header, seamless Light/Dark Mode switching, and centralized badge styling.
* **Search & Logic:** Client-side logic powered by **Dictionary Compressed JSON Assets** (`search_index.json`, `rescues.json`, `trends.json`) to minimize payload size. Features include **Infinite Scroll (Intersection Observer)**, **DOM Batching**, **Mutually Exclusive Filters**, and client-side data hydration.
* **CI/CD:** GitHub Actions with **Playwright caching** (no Selenium/Chrome deps), deploying to an external public repository. Includes "Fast Mode" workflows.

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Async orchestrator implementing a **Timeboxed Circuit Breaker** pattern. It manages blocking scraper calls, enforces a 15-minute timeout on Facebook scraping, records the **Daily Population Snapshot**, and handles the pipeline. Supports CLI flags like `--skip-facebook` for fast updates.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: **Playwright (Crawlee)** scraper for primary CACC portal discovery. Features robust iframe extraction logic, hydration waits, and session cookie capture for Phase 2.
    * `src/fb_crawler.py`: **Crawlee/Playwright** scraper implementing the "Embed Proxy" strategy.
    * `src/parser.py`: Regex logic to parse dog descriptions and extract attributes.
    * `src/storage.py`: **DuckDB-backed** storage engine. Handles complex merge logic (preserving intake dates) via SQL `ON CONFLICT` clauses and ensures unique constraints.
    * `src/models.py`: Defines the `Dog` dataclass.
    * `src/geo.py`: Geocoding service using `geopy` with persistent JSON caching.

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/stats.py`: Primary data engine. Implements **Centralized Ghost Record Detection** to resolve data quality issues by prioritizing "Good" statuses and older IDs. Injectable DataFrames for memory optimization.
    * `src/analytics/charts.py`: Pure data transformation module. Prepares JSON-serializable structures for the frontend.
    * `src/analytics/population.py`: Manages `population_history.csv` to track the ground-truth count of active dogs daily.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Logic for status normalization and report generation. Consumes "Clean" data from Analytics to avoid duplicate logic. Generates compressed JSON assets.
    * `templates/base.html`: **Master Layout** with global utility classes.
    * `templates/partials/navbar.html`: **Theme Source & Nav.** Defines Global CSS Variables.
    * `templates/partials/chart_setup.html`: **Chart Configuration.** Centralized Chart.js defaults.
    * `templates/index.html`: **Main Dashboard.** Features Infinite Scroll and client-side hydration.
    * `templates/trends.html`: **Analytics Dashboard.** Features a **Global Date Range Selector**.
    * `templates/rescues.html`: **Partner Analytics.** Interactive bar chart with drill-down.
    * `templates/removed.html`: "Lost/Unaccounted" report, filtered against "Ghost" duplicates.
    * `templates/breeds.html`: Breed-specific statistics and outcome tables.
    * `templates/map_overlay.html`: **Standalone Overlay** injected into the Folium map.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Hourly job. Full scraping pipeline (Phase 1-3).
    * `scrape-fast.yml`: Manual trigger. Skips Facebook scraping for rapid data updates.
    * `refresh_code.yml`: Manual trigger to regenerate site/assets without scraping.
    * `scrape-facebook-only.yml`: Workflow for testing Crawlee isolation.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.