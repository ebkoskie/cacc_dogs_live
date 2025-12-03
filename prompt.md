### Prompt for New Conversation: "CACC Dog Bot - Comprehensive Project Context"

**Context & Goal:**
I am building `cacc_dogs`, a Python-based static site generator that scrapes, tracks, and visualizes dog adoption data from Chicago Animal Care & Control (CACC). My goal is to provide a high-performance, user-friendly dashboard for volunteers.

**Technical Stack:**
* **Language:** Python 3.12
* **Scraper:**
    * **Phase 1 (Discovery):** SeleniumBase (Stealth Mode) for robust ID collection from the CACC portal.
    * **Phase 2 (Details):** `aiohttp` for high-speed async data fetching of animal details.
    * **Phase 3 (Enrichment):** **Crawlee + Playwright** using an **Embed Proxy Strategy** to bypass Facebook login walls and aggregate multiple media links.
* **Data Persistence:** Optimized CSV files (`dogs_active.csv`, `dogs_historic.csv`) tracking essential fields.
* **Visualization:**
    * **Interactive:** `Chart.js` for responsive, client-side charts (Trends, Rescues).
    * **Static:** `matplotlib` generating PNG snapshots for historical archiving.
    * **Mapping:** Leaflet.js with client-side clustering and spatial indexing.
* **Frontend:** Jinja2 templating generating static HTML with a responsive **Tile Grid** UI supporting multiple media links per card.
* **Search & Logic:** Client-side logic powered by `search_index.json`. Features include **Multi-Select Filtering**, **Smart Sorting**, **Drill-Down Analytics**, **Archive Modes**, and **Dictionary Compression** to optimize data payloads.
* **CI/CD:** GitHub Actions with **Playwright caching**, `xvfb` support for headless browsing, deploying to an external public repository.

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Async orchestrator using `asyncio.to_thread` to manage blocking scraper calls alongside async enrichment. Handles the pipeline: Scrape -> Storage -> Analytics -> Report -> Map -> Minification.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: SeleniumBase scraper for primary CACC portal discovery and ID extraction.
    * `src/fb_crawler.py`: **Crawlee/Playwright** scraper implementing the "Embed Proxy" strategy. Harvests URLs from the public grid and visits lightweight `plugins/post.php` embeds to extract captions and media without hitting login walls. Aggregates links into pipe-separated strings.
    * `src/parser.py`: Regex logic to parse dog descriptions and extract attributes.
    * `src/storage.py`: Manages CSV reading/writing with schema versioning support.
    * `src/models.py`: Defines the `Dog` dataclass (includes `facebook_url` as a combined string and transient flags).
    * `src/geo.py`: Geocoding service using `geopy` with persistent JSON caching.

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/stats.py`: **Dual-Mode Engine.** Generates dynamic JSON for interactive charts AND triggers static PNG generation. Includes logic for "Active Cohort" LOS analysis.
    * `src/analytics/charts.py`: Generates legacy static PNG charts (Intake Trends, LOS, Outcomes) to `assets/`.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Logic for status normalization (RTO/Rescued/Adopted), timezone conversion (Chicago), and report generation. Implements **Dictionary Compression** (lookup tables for partners/breeds) to minimize `search_index.json` size.
    * `templates/index.html`: **Main Dashboard.** Tile grid with advanced filters, "Ghost" badging, and multi-link Facebook dropdowns. Supports "Archive Mode" for adopted/rescued dogs.
    * `templates/trends.html`: **Analytics Dashboard.** Features interactive charts (LOS Cohorts, Daily Intakes) and a "Frosted Glass" spoiler for sensitive euthanasia data.
    * `templates/rescues.html`: **Partner Analytics.** Interactive bar chart with "Click-to-Drill-Down" functionality revealing breed distribution pie charts, plus a **"Recent Rescues"** section displaying the last 7 days of activity in a responsive tile grid.
    * `templates/removed.html`: "Lost/Unaccounted" report filtering out known positive outcomes (Adoptions/Rescues).
    * `templates/breeds.html`: Breed-specific statistics and outcome tables.
    * `templates/map_overlay.html`: Leaflet map logic.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Hourly job. Caches and installs **Playwright browsers**, runs scraper, commits data to private repo, and deploys artifacts to **public external repo** (`cacc_dogs_live`) via PAT.
    * `refresh_code.yml`: Manual trigger to regenerate site/assets without scraping (syncs dependencies with main workflow).
    * `scrape-facebook-only.yml`: Specialized workflow for testing and debugging the Crawlee implementation in isolation.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status to protect intellectual property and liability.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.