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
* **Frontend:** Jinja2 templating with a **Global CSS Variable Design System**. Features a responsive "Frosted Glass" sticky header, seamless Light/Dark Mode switching, and centralized badge styling.
* **Search & Logic:** Client-side logic powered by **Dictionary Compressed JSON Assets** (`search_index.json`, `rescues.json`, `trends.json`) to minimize payload size. Features include **Infinite Scroll (Intersection Observer)**, **DOM Batching**, **Mutually Exclusive Filters**, and client-side data hydration.
* **CI/CD:** GitHub Actions with **Playwright caching**, `xvfb` support for headless browsing, deploying to an external public repository.

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Async orchestrator implementing a **Timeboxed Circuit Breaker** pattern. It manages blocking scraper calls via `asyncio.to_thread`, enforces a strict 15-minute timeout on the optional Facebook scraping phase to prevent pipeline hangs, and handles the pipeline: Scrape -> Storage -> Analytics -> Report -> Map -> Minification.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: SeleniumBase scraper for primary CACC portal discovery and ID extraction.
    * `src/fb_crawler.py`: **Crawlee/Playwright** scraper implementing the "Embed Proxy" strategy. Harvests URLs from the public grid and visits lightweight `plugins/post.php` embeds to extract captions and media without hitting login walls. Aggregates links into pipe-separated strings.
    * `src/parser.py`: Regex logic to parse dog descriptions and extract attributes.
    * `src/storage.py`: Manages CSV reading/writing with schema versioning support.
    * `src/models.py`: Defines the `Dog` dataclass (includes `facebook_url` as a combined string and transient flags).
    * `src/geo.py`: Geocoding service using `geopy` with persistent JSON caching.

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/stats.py`: **Dual-Mode Engine.** Generates dynamic JSON structures for interactive charts AND triggers static PNG generation. Includes logic for **Historical Time to Outcome** (Median LOS) analysis.
    * `src/analytics/charts.py`: Generates legacy static PNG charts (Intake Trends, LOS, Outcomes) to `assets/`.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Logic for status normalization (RTO/Rescued/Adopted), timezone conversion (Chicago), and report generation. Implements **Dictionary Compression** (mapping repetitive strings to integers) and generates externalized JSON assets (`search_index.json`, `rescues.json`, `trends.json`) to unblock rendering.
    * `templates/base.html`: **Master Layout.** Defines the skeleton, footer, and **Global Utility Classes** (e.g., `.tag`, `.status-badge`) used across all child pages.
    * `templates/partials/navbar.html`: **Theme Source & Nav.** Defines the **Global CSS Variables** (`:root`) for the design system (Colors, Light/Dark mode overrides) and the navigation structure. Included by `base.html` and `map_overlay.html` to ensure consistent theming.
    * `templates/index.html`: **Main Dashboard (Extends Base).** Features **Infinite Scroll** via Intersection Observer, optimized DOM batching for large datasets, advanced mutually exclusive filters (e.g., Puppy vs Senior), and client-side hydration of compressed data.
    * `templates/trends.html`: **Analytics Dashboard (Extends Base).** Fetches `trends.json` asynchronously. Features interactive charts (**Median LOS Trends**, Daily Intakes) and a "Frosted Glass" spoiler for sensitive euthanasia data.
    * `templates/rescues.html`: **Partner Analytics (Extends Base).** Fetches `rescues.json` asynchronously. Interactive bar chart with "Click-to-Drill-Down" functionality revealing breed distribution pie charts, plus a **"Recent Rescues"** section.
    * `templates/removed.html`: "Lost/Unaccounted" report (Extends Base) filtering out known positive outcomes.
    * `templates/breeds.html`: Breed-specific statistics and outcome tables (Extends Base).
    * `templates/map_overlay.html`: **Standalone Overlay.** Injected into the Folium map. Fetches compressed `map_data.json`. Includes `partials/navbar.html` to inherit the global theme variables and search styles.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Hourly job. Caches and installs **Playwright browsers**, runs scraper, commits data to private repo, and deploys artifacts to **public external repo** (`cacc_dogs_live`) via PAT.
    * `refresh_code.yml`: Manual trigger to regenerate site/assets without scraping (syncs dependencies with main workflow).
    * `scrape-facebook-only.yml`: Specialized workflow for testing and debugging the Crawlee implementation in isolation.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status to protect intellectual property and liability.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.