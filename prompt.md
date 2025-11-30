### Prompt for New Conversation: "CACC Dog Bot - Comprehensive Project Context"

**Context & Goal:**
I am building `cacc_dogs`, a Python-based static site generator that scrapes, tracks, and visualizes dog adoption data from Chicago Animal Care & Control (CACC). My goal is to provide a high-performance, user-friendly dashboard for volunteers.

**Technical Stack:**
* **Language:** Python 3.12
* **Scraper:** Selenium (Phase 1: ID collection) + `aiohttp` (Phase 2: Async detail fetching).
* **Data Persistence:** Optimized CSV files (`dogs_active.csv`, `dogs_historic.csv`) tracking essential fields only.
* **Visualization:** * `matplotlib` (static charts optimized as PNGs).
    * `folium` (base map tile generation).
    * **Leaflet.js + Client-Side Logic** (Dynamic pin rendering, clustering, and spatial indexing).
    * `Chart.js` (client-side interactive charts).
* **Frontend:** Jinja2 templating generating static HTML.
    * **UI Architecture:** Responsive **Tile Grid** system with "Ghost" badges and client-side interactions.
* **Search & Logic:** Advanced Client-side logic powered by `search_index.json` (Dashboard) and `map_data.json` (Map). Features include **Multi-Select Filtering**, **Smart Sorting** (context-aware defaults), and **Archive Modes** (RTO/Rescued).
* **CI/CD:** GitHub Actions (`scrape.yml` for hourly updates, `refresh_code.yml` for manual logic updates).

**Complete Architecture & File Manifest:**

1.  **Entry Point:**
    * `main.py`: Orchestrates the flow: Scrape -> Storage -> Analytics -> Report -> Map Generation -> Minification.

2.  **Scraping & Data Logic (`src/`):**
    * `src/scraper.py`: Hybrid Selenium/aiohttp scraper.
    * `src/parser.py`: Regex logic to parse dog descriptions.
    * `src/storage.py`: Manages CSV reading/writing (Dynamically handles schema changes).
    * `src/models.py`: Defines the `Dog` dataclass (includes transient `mappable` flag and age parsing).
    * `src/geo.py`: Geocoding service using `geopy` with persistent caching (`geocache.json`).

3.  **Analytics & Visualization (`src/analytics/`):**
    * `src/analytics/charts.py`: Generates static PNG charts (Intake Trends, LOS, Outcomes) to `assets/`.
    * `src/analytics/stats.py`: Prepares data for charts.

4.  **Reporting & Templates (`src/report.py` & `templates/`):**
    * `src/report.py`: Verifies geocoding status, generates `search_index.json` (with Age/Mappable data), and builds all HTML reports.
    * `src/maps.py`: Generates the map skeleton (`map.html`) and the external data file (`map_data.json`).
    * `templates/index.html`: **Main Dashboard.** Features a responsive Tile Grid, Smart Sorting, Multi-select filters (Puppy, Senior, Stray, Long Stay, RTO, Rescued), and "Ghost" styling for tags. Includes legal disclaimer footer.
    * `templates/trends.html`: **New Analytics Page.** dedicated to Intake, LOS, and Outcome charts.
    * `templates/map_overlay.html`: **Client-side logic** injected into the map. Handles lazy loading, spatial indexing, and search.
    * `templates/rescues.html`, `templates/breeds.html`, `templates/removed.html`: Sub-pages with specific statistics and tables.

5.  **Deployment Workflows (`.github/workflows/`):**
    * `scrape.yml`: Runs hourly. Scrapes data, generates site/assets, commits to private repo, and deploys to public repo.
    * `refresh_code.yml`: Regenerates site/assets without scraping and deploys.

**Legal Compliance:**
* All pages include a footer disclaimer clarifying volunteer independence and "as-is" data status to protect intellectual property and liability.

Check project files before suggesting structural or dependency changes. Provide full file outputs for the relevant files when changes are needed. Provide single line git commit message for all changes.