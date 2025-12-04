### Prompt for New Conversation: "CACC Dog Bot - Comprehensive Project Context"

**Context & Goal:**
I am building `cacc_dogs`, a Python-based static site generator that scrapes, tracks, and visualizes dog adoption data from Chicago Animal Care & Control (CACC). My goal is to provide a high-performance, user-friendly dashboard for volunteers.

**Technical Stack:**
* **Language:** Python 3.12
* **Scraper:**
    * **Phase 1 (Discovery):** SeleniumBase (Stealth Mode) for robust ID collection from the CACC portal.
    * **Phase 2 (Details):** `aiohttp` for high-speed async data fetching of animal details.
    * **Phase 3 (Enrichment):** **Crawlee + Playwright** using an **Embed Proxy Strategy** to bypass Facebook login walls and aggregate multiple media links.
* **Data Persistence:** Optimized CSV files (`dogs_active.csv`, `dogs_historic.csv`, `population_history.csv`) tracking essential fields.
* **Visualization:**
    * **Interactive:** `Chart.js` for all client-side charts (Trends, Rescues, Population).
    * **Mapping:** Leaflet.js with client-side clustering and spatial indexing.
* **Frontend:** Jinja2 templating with a **Global CSS Variable Design System**. Features a responsive "Frosted Glass" sticky header, seamless Light/Dark Mode switching, and centralized badge styling.
* **Search & Logic:** Client-side logic powered by **Dictionary Compressed JSON Assets** (`search_index.json`, `rescues.json`, `trends.json`) to minimize payload size. Features include **Infinite Scroll (Intersection Observer)**, **DOM Batching**, **Mutually Exclusive Filters**, and client-side data hydration.
* **CI/CD:** GitHub Actions with **Playwright caching**, `xvfb` support for headless browsing, deploying to an external public repository.

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Async orchestrator implementing a **Timeboxed Circuit Breaker** pattern. It manages blocking scraper calls, enforces a 15-minute timeout on Facebook scraping, records the **Daily Population Snapshot**, and handles the pipeline: Scrape -> Storage -> Analytics -> Report -> Map -> Minification.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: SeleniumBase scraper for primary CACC portal discovery and ID extraction.
    * `src/fb_crawler.py`: **Crawlee/Playwright** scraper implementing the "Embed Proxy" strategy.
    * `src/parser.py`: Regex logic to parse dog descriptions and extract attributes.
    * `src/storage.py`: Manages CSV reading/writing with schema versioning support.
    * `src/models.py`: Defines the `Dog` dataclass.
    * `src/geo.py`: Geocoding service using `geopy` with persistent JSON caching.

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/stats.py`: Primary data engine. Implements **Ghost Record Detection** (Fuzzy Deduplication) to resolve data quality issues (e.g., re-intakes getting new IDs) by prioritizing "Good" statuses and older IDs.
    * `src/analytics/charts.py`: Pure data transformation module. Prepares JSON-serializable structures for the frontend, calculating cumulative **Shelter Population** (Inventory), daily flows, and zero-filling timelines.
    * `src/analytics/population.py`: Manages `population_history.csv` to track the ground-truth count of active dogs daily, preventing drift in the population chart.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Logic for status normalization, timezone conversion, and report generation. Generates compressed JSON assets. Applies **Ghost Filtering** to the "Removed" list to ensure accuracy.
    * `templates/base.html`: **Master Layout** with global utility classes.
    * `templates/partials/navbar.html`: **Theme Source & Nav.** Defines Global CSS Variables.
    * `templates/partials/chart_setup.html`: **Chart Configuration.** Centralized Chart.js defaults (colors, fonts, grid styles) used by Trends and Rescues pages.
    * `templates/index.html`: **Main Dashboard.** Features Infinite Scroll, DOM batching, and client-side hydration.
    * `templates/trends.html`: **Analytics Dashboard.** Features a **Global Date Range Selector** (default 7 days). Displays interactive time-series charts for **Shelter Population**, **Intake vs. Outcomes**, **Outcomes by Type**, and **Median LOS**. Uses dashed lines to indicate incomplete data for the current day.
    * `templates/rescues.html`: **Partner Analytics.** Interactive bar chart with drill-down functionality.
    * `templates/removed.html`: "Lost/Unaccounted" report, filtered against "Ghost" duplicates.
    * `templates/breeds.html`: Breed-specific statistics and outcome tables.
    * `templates/map_overlay.html`: **Standalone Overlay** injected into the Folium map.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Hourly job. Caches Playwright, runs scraper, commits data, and deploys to public repo.
    * `refresh_code.yml`: Manual trigger to regenerate site/assets without scraping.
    * `scrape-facebook-only.yml`: Workflow for testing Crawlee in isolation.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.