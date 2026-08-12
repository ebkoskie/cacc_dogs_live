# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Scraper + static-site generator for Chicago Animal Care & Control adoptable dogs. A Python pipeline scrapes 24petconnect.com, enriches dogs with social-media links (Facebook/Instagram/YouTube), geocodes stray found-locations, computes analytics, and renders a static site that CI publishes to the public repo `ebkoskie/cacc_dogs_live` (GitHub Pages). Two Cloudflare Worker subprojects live in the monorepo: `pavilion-worker/` (OCR of handwritten kennel walk-sheets → location badges) and `scrape-scheduler/` (cron that triggers the scrape workflows).

## Commands

Python is managed with uv (pinned to 0.9.15 via `pyproject.toml`; `package = false`, so no install of the project itself).

```bash
uv sync --no-install-project          # install deps
uv run python main.py --skip-scrape   # rebuild the site from existing CSVs — the local dev loop for template/report changes
uv run python main.py                 # full pipeline incl. live scrape (needs: uv run playwright install chromium)
uv run python main.py --skip-facebook # scrape but skip FB/IG/YT ("fast mode"; exits early if no data changed)
```

Tests — **pytest is not a project dependency**; inject it with `--with`. Always exclude `tests/test_api_mocks.py`: it is an untracked leftover from a past review session whose Playwright frontend tests are stale against the current templates and fail with 30s timeouts — its failures are never regressions.

```bash
uv run --with pytest pytest --ignore=tests/test_api_mocks.py   # full suite (112 tests, passes)
uv run --with pytest pytest tests/test_pavilions.py -k name    # one file / one test
```

Lint: `uvx ruff check src/` (no config file; default rules). **No CI workflow runs tests or lint**, and a push touching `templates/` or `main.py` auto-deploys to production via `refresh_code.yml` — run pytest/ruff locally before pushing.

Chart-correctness validators (independent pandas re-computation vs the production DuckDB queries): `uv run python scripts/validate_los_chart.py` and `scripts/validate_outcome_charts.py`.

Workers (each has its own `package.json`; deploys are manual, there is no CI deploy):

```bash
cd pavilion-worker && npm run typecheck && npm run dry-run   # same for scrape-scheduler/
npm run deploy                                               # wrangler deploy
```

## Architecture

`main.py` orchestrates the pipeline; the stages live in `src/`:

1. **Scrape** — `scraper.py`: phase 1 lists dogs via Crawlee/Playwright (stealth), phase 2 enriches detail pages via aiohttp. A **safety gate aborts the run if 0 dogs are found** so an upstream outage never wipes existing data. An empty `description` is the sentinel for "error page": such dogs are dropped from `current_dogs` and flow into removed IDs — parser changes must keep `description` populated for real dogs. Shared browser config in `crawler_utils.py`.
2. **Social enrichment (parallel, individually time-bounded)** — `fb_crawler.py`, `ig_crawler.py`, `youtube.py` run concurrently with per-task `asyncio.wait_for` timeouts (constants at the top of `main.py`); a timeout salvages partial results rather than failing the run. Env gates: `YOUTUBE_API_KEY`/`YOUTUBE_CHANNEL_ID` (secrets set only in scrape.yml — a local full run silently gets zero YouTube links), `INSTAGRAM_HANDLE` (default `chicagoshelterdogs`; empty disables IG); the Facebook page is hardcoded (`facebook.com/CACCDogs`), no credentials. Geocoding (`geo.py` → `geocache.json`) prefetches in parallel too.
3. **Persist** — `storage.py`: CSVs are the database (`dogs_active.csv`, `dogs_historic.csv`, `social_links.csv`), merged with in-memory DuckDB. See "Data-layer invariants" below.
4. **Pipeline stages** — `pipeline.py` holds extracted, testable stage functions (social-link enrichment, name-change/FKA detection, stray-data preservation, population counts).
5. **Analytics** — `src/analytics/` (pandas + DuckDB stats, chart data, population tracking → `population_history.csv`).
6. **Report** — `report.py` renders Jinja2 `templates/` into root-level HTML plus `site_data.json` (the single data payload; trends analytics are inlined into `trends.html` as `trends_json`), minified with htmlmin. `maps.py` builds the folium `map.html`, `map_data.json`, and `stray311.json` (Chicago Open311 stray-complaint snapshot; optional `OPEN311_API_KEY`) — the Open311 call is **deliberately plain http** because the city API host's TLS cert fails verification, and any fetch failure writes an empty snapshot rather than failing the build.

The `Dog` dataclass in `models.py` is the single record type; IDs match `^A\d{5,7}$`. Timestamps use `America/Chicago`, except `stray311.json`'s `updated` field and query window, which are deliberately UTC/ISO-8601-Z for client-side localization. `main.py`/`storage.py`/`pipeline.py` log via `print` with GitHub Actions workflow commands (`::group::`, `::notice::`, `::error::`); the crawler modules (`scraper.py` internals, `fb_crawler.py`, `ig_crawler.py`, `youtube.py`) use `logging` loggers — keep each style where it is, and never emit `::group::` from inside the timeout-bounded social tasks (main.py owns those markers so a cancelled task can't strand an unclosed group).

### Data-layer invariants

- **Adding a Dog field/CSV column is a three-site change in `storage.py`**: an ALTER TABLE migration in `update_historic` (existing pattern in the file), a `keep_nonempty_cols` decision, and the hard-coded `expected_order`/`col_order` lists in `_fix_column_swap_in_file` — that repair routine runs at every pipeline start and rewrites both CSVs with only its listed columns, **silently dropping any column it doesn't know about**.
- `keep_nonempty_cols` protects only a specific set of columns in `dogs_historic.csv` (Intake Date, Found At, Stray Hold Date, is_chipped, and the three social-URL columns) from being overwritten by empty scraped values; **all other columns are last-writer-wins, empty included**. The mirror merge in `main.py` (in-memory, analytics only, never persisted) applies keep-nonempty to every field.
- `social_links.csv` is the **accumulate-only source of truth** for social links: rows keyed (dog_id, url) are upserted, never deleted, and `enrich_social_links` rewrites the per-dog social columns wholesale from it each run — a bad link must be removed by editing that CSV, not by re-scraping. Link strings flow as `" | "`-joined URLs; YouTube entries carry a `url~Label` suffix.
- Fast mode's no-change early exit compares only id → (Status, Outcome Date); changes to any other field don't trigger a rebuild.
- `population_history.csv` gets one row per Chicago day, written **only during live scrapes** — `--skip-scrape` rebuilds never update it.

### Analytics gotchas

Two distinct "ghost" mechanisms: `stats.py:_remove_ghost_records` dedupes duplicate historic records (name + intake-date, preferring positive-outcome/active records), while `charts.py:_apply_ghost_fix`/`_removed_mask` treat a dog absent from the active list with no Outcome Date as departing on its last `scrape_date`. Every trend chart relies on that scrape_date fallback — dropping it silently inflates population/LOS numbers (the validators' monotonic-LOS sanity check exists to catch this). The population chart layers three sources in precedence order: DuckDB census from historic data < `population_history.csv` snapshots < today's live count from `dogs_active.csv`.

### Frontend contract

- `site_data.json` is a **compressed contract**: `report.py` serializes dogs/rescues with 1–2 letter keys hydrated via frequency-sorted meta lookup lists and URL-prefix compression, decoded by `assets/js/decompress.js`. Falsy nullable fields are stripped, but index fields (`a`/`c`/`p`) never are — 0 is a valid lookup index. Any serializer change must be mirrored in `templates/index.html`, `templates/upload.html` (admin panel), and `decompress.js`.
- Dates: `base.html` defines site-wide helpers (`siteToday`, `siteDateTs`, `siteDayDiff`, `formatSiteDate`) treating every `YYYY-MM-DD` as a UTC-midnight calendar date with "today" computed in America/Chicago — use them in templates instead of raw `Date` math or displayed days drift by viewer timezone.
- Theming: the `:root` CSS variables (dark default) and `body.light-mode` overrides live in `templates/partials/navbar.html`, not base.html. Chart pages include `partials/chart_setup.html`, which remaps dark-mode chart colors to light via the hard-coded `colorMapLight` table — a new chart color must be added there or it silently stays dark in light mode.
- Env-gated rendering: `POSTHOG_API_KEY` empty omits the snippet; even when set, PostHog initializes only on `*.cacc.dog` hostnames (silent no-op locally) — fire events via base.html's `track()` wrapper. `PAVILION_API_BASE`/`TURNSTILE_SITE_KEY` reach every page via `_render_page` and show/hide the badge-report dialog, upload form, and Turnstile widgets.
- `akc-data-latest.csv` is a committed **static source file** (AKC breed weights, unlike the neighboring generated files) used by `report.py` for the Small-dog filter and size categories; CACC→AKC name matching lives in `_BREED_OVERRIDES`.

### Generated vs. source files

Root-level `*.html`, `site_data.json`, `map_data.json`, `stray311.json`, etc. are **build outputs** (gitignored) — edit `templates/` instead. `README.md` is also generated by the pipeline; don't hand-edit it. Root-level `search_index.json`, `rescues.json`, and `trends.json` are stale outputs of an older build that nothing generates or reads anymore. The data CSVs and `geocache.json` at the root are the persistent datastore, committed by CI. `scratch/`, `.agents/`, `PROJECT.md`, `ORIGINAL_REQUEST.md`, `code_review_report.md`, `prompt.md` (early project doc describing long-gone hourly-cron/Docker architecture), `skills-lock.json`, and `tests/test_api_mocks.py` are stale artifacts, not authoritative docs.

### CI / deployment (.github/workflows/)

GitHub cron proved unreliable, so the `scrape-scheduler` Worker fires `repository_dispatch` events instead: `scrape-full` → `scrape.yml` (every 6h at :15 UTC), `scrape-fast` → `scrape-fast.yml` (every 30 min during Chicago business hours, runs `--skip-facebook`). Both commit data CSVs to this private repo, then publish the site to `ebkoskie/cacc_dogs_live`. The two workflows use separate concurrency groups and can race on `git push` — **both** carry a byte-identical replay-on-new-head push loop (kept in sync manually); `promote_corrections.yml` instead uses `git pull --rebase`, safe because it only touches `data/` files no scraper writes. `refresh_code.yml` rebuilds without scraping (on pushes to `templates/`/`main.py`, and on `pavilion-upload` dispatch from the worker). `promote_corrections.yml` runs daily, lifting learned aliases/audit log from the worker's KV into `data/`.

Two hardcoded file lists bite when adding files: (1) scrape.yml and scrape-fast.yml `git add` an explicit allowlist of data files — a new persistent datastore file must be added to **both** or CI silently never commits it and its history is lost every run; (2) all three deploy workflows publish the repo root with an `exclude_assets` denylist — a new root-level source/data file must be added to that list in **all three** or it gets published to the public site.

### Pavilion location badges

**`docs/pavilion-worker.md` is the contract and source of truth** — `pavilion-worker/` (Cloudflare Worker + KV + Gemini Vision OCR + Turnstile) implements it exactly, and `src/pavilions.py` (badge resolution with layered precedence: admin override > crowd consensus > OCR sheet) and `scripts/promote_corrections.py` consume it. Change the contract doc and both sides together. `hl_history.py` persists last-known walker-level highlights (yellow/orange) to `data/hl_history.json` so the Removed page keeps them after a dog leaves. The build degrades gracefully when the worker env (`PAVILION_API_BASE`, `PAVILION_DATA_TOKEN`, `TURNSTILE_SITE_KEY`) is absent — badges just don't render.
