### Prompt for New Conversation: "CACC Dog Bot - Comprehensive Project Context"

**Context & Goal:**
I am building `cacc_dogs`, a Python-based static site generator that scrapes, tracks, and visualizes dog adoption data from Chicago Animal Care & Control (CACC). My goal is to provide a high-performance, user-friendly dashboard for volunteers.

**Technical Stack:**
* **Language & Management:** Python 3.12 managed by **`uv`** (replacing pip/requirements.txt) for ultra-fast resolution and locking (`uv.lock`).
* **Scraper:**
    * **Phase 1 (Discovery):** **Playwright (Crawlee)** with **Stealth Mode** (Fingerprint generation) for robust ID collection.
    * **Phase 2 (Details):** `aiohttp` for high-speed async data fetching of animal details (cookies inherited from Phase 1).
    * **Phase 3 (Enrichment):**
        * **Facebook:** **Crawlee + Playwright** using an **Embed Proxy Strategy** to bypass login walls and aggregate media.
        * **YouTube:** **YouTube Data API v3** via `aiohttp`. Features **Time-Aware Smart Matching** (Regex ID + **Robust Case-Insensitive** Name/Intake Date validation) to link videos (including Shorts) to dogs. Also implements **Video Label Detection** to categorize content (e.g., "Leash Test", "Playgroup").
* **Data Persistence:** **Hybrid DuckDB + CSV**. Uses DuckDB for high-performance in-memory SQL merging (`UPSERT` logic) and distinct record processing, while outputting optimized CSVs (`dogs_active.csv`, `dogs_historic.csv`) for the frontend.
* **Visualization:**
    * **Interactive:** `Chart.js` for all client-side charts (Trends, Rescues, Population).
    * **Mapping:** Leaflet.js with client-side clustering and spatial indexing.
* **Frontend:** Jinja2 templating with a **Global CSS Variable Design System**. Features a responsive "Frosted Glass" sticky header, seamless Light/Dark Mode switching, centralized badge styling, and integrated **Smart Social Media Buttons** (YouTube/Facebook with label support).
* **Search & Logic:** Client-side logic powered by **Dictionary Compressed JSON Assets** (`search_index.json`, `rescues.json`, `trends.json`) to minimize payload size. Features include **Infinite Scroll (Intersection Observer)**, **DOM Batching**, **Mutually Exclusive Filters**, and client-side data hydration.
* **CI/CD:** GitHub Actions optimized with **`uv`** caching. Scrapers run inside **Official Playwright Docker Containers** (e.g., `v1.57.0-noble`) to eliminate system dependency installation time.

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Async orchestrator implementing a **Timeboxed Circuit Breaker** pattern. It manages blocking scraper calls, enforces a 15-minute timeout on Facebook scraping, runs **Concurrent YouTube Fetching**, records the **Daily Population Snapshot**, and handles the pipeline.
    * `pyproject.toml`: Project configuration and dependency definition.
    * `uv.lock`: Strictly locked dependency tree for reproducible builds.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: **Playwright (Crawlee)** scraper for primary CACC portal discovery. Features robust iframe extraction logic, hydration waits, and session cookie capture.
    * `src/fb_crawler.py`: **Crawlee/Playwright** scraper implementing the "Embed Proxy" strategy for Facebook.
    * `src/youtube.py`: **Async API Fetcher** for the channel's "Uploads" playlist. Implements dual-strategy matching: Explicit ID match vs. **Case-Insensitive** Temporal Name match. Features **Video Label Detection** (scanning titles/descriptions) to auto-label "Leash Tests" and "Playgroups".
    * `src/parser.py`: Regex logic to parse dog descriptions and extract attributes.
    * `src/storage.py`: **DuckDB-backed** storage engine. Handles complex merge logic via SQL `ON CONFLICT` clauses.
    * `src/models.py`: Defines the `Dog` dataclass (includes `youtube_urls`, `facebook_url`, and **`aka`** for previous names).
    * `src/geo.py`: Geocoding service using `geopy` with persistent JSON caching.

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/stats.py`: Primary data engine. Implements **Centralized Ghost Record Detection** to resolve data quality issues.
    * `src/analytics/charts.py`: Pure data transformation module. Prepares JSON-serializable structures.
    * `src/analytics/population.py`: Manages `population_history.csv` to track the ground-truth count of active dogs daily.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Logic for status normalization and report generation. Exports `youtube_urls` (key `"y"`) and `aka` (key `"k"`) to the compressed search index.
    * `templates/base.html`: **Master Layout** with global utility classes.
    * `templates/partials/navbar.html`: **Theme Source & Nav.** Defines Global CSS Variables.
    * `templates/partials/chart_setup.html`: **Chart Configuration.** Centralized Chart.js defaults.
    * `templates/index.html`: **Main Dashboard.** Features Infinite Scroll, client-side hydration, **AKA Name Toggling**, and **Labeled Media Dropdowns**.
    * `templates/trends.html`: **Analytics Dashboard.** Features a **Global Date Range Selector**.
    * `templates/rescues.html`: **Partner Analytics.** Interactive bar chart with drill-down.
    * `templates/removed.html`: "Lost/Unaccounted" report, filtered against "Ghost" duplicates.
    * `templates/breeds.html`: Breed-specific statistics and outcome tables.
    * `templates/map_overlay.html`: **Standalone Overlay** injected into the Folium map.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Hourly job. Full scraping pipeline using `uv` inside a Playwright Container. Injects **YouTube API Secrets**.
    * `scrape-fast.yml`: Manual trigger. Containerized fast scrape (skips Facebook/YouTube).
    * `refresh_code.yml`: Manual trigger to regenerate site/assets without scraping.
    * `scrape-facebook-only.yml`: Workflow for testing Crawlee isolation.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.