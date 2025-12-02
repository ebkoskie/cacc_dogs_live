# Crawlee Migration Guide

## Overview

This document describes the migration from SeleniumBase to Crawlee/Playwright for Facebook scraping in the CACC Dogs project.

## What Changed

### Before (SeleniumBase)
- Used `seleniumbase` with undetected-chromedriver mode
- Single-threaded synchronous scraping
- Login walls frequently blocked content
- Success rate: ~20%
- Complex popup dismissal logic required

### After (Crawlee/Playwright)
- Uses `crawlee[playwright]` with built-in anti-detection
- Async/await architecture for better performance
- Better fingerprint management (automatic)
- Target success rate: >80%
- Cleaner, more maintainable code

## Architecture

```
CACCScraper (src/scraper.py)
├── fetch_facebook_data_crawlee() [NEW] - Primary method using Crawlee
└── fetch_facebook_data() [DEPRECATED] - Legacy SeleniumBase fallback

CACCFacebookCrawler (src/fb_crawler.py) [NEW]
├── scrape_all_sources() - Main entry point
├── scrape_videos() - Videos page scraping
├── scrape_photos() - Photo album scraping
└── _navigate_photo_viewer() - Photo viewer navigation
```

## Key Features

### 1. Anti-Detection
Crawlee automatically handles:
- Browser fingerprinting (canvas, WebGL, fonts, etc.)
- User agent rotation
- Realistic timing patterns
- HTTP header management

### 2. Async Architecture
```python
# Old (sync)
fb_data = await asyncio.to_thread(scraper.fetch_facebook_data)

# New (async)
fb_data = await scraper.fetch_facebook_data_crawlee()
```

### 3. Automatic Fallback
If Crawlee fails, the system automatically falls back to the old SeleniumBase method:

```python
try:
    crawler = CACCFacebookCrawler(headless=self.headless)
    fb_links = await crawler.scrape_all_sources()
    return fb_links
except Exception as e:
    print(f"  ❌ Crawlee scraping failed: {e}")
    print("  ⚠️ Falling back to SeleniumBase method...")
    return self.fetch_facebook_data()
```

## Installation

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### GitHub Actions
The workflow automatically installs Playwright:
```yaml
- name: 📦 Install Python Dependencies
  run: |
    pip install -r requirements.txt
    seleniumbase install chromedriver
    playwright install chromium
    playwright install-deps chromium
```

## Usage

### Basic Usage
```python
from src.scraper import CACCScraper

scraper = CACCScraper(headless=True)

# Use new Crawlee method (recommended)
fb_data = await scraper.fetch_facebook_data_crawlee()

# Results: {dog_id: facebook_url}
# Example: {"A123456": "https://m.facebook.com/CACCDogs/videos/123..."}
```

### Standalone Testing
Test the Crawlee scraper independently:
```bash
# Quick test (headless mode)
python test_crawlee.py

# Test with visible browser (for debugging)
python test_crawlee.py --no-headless

# Test only videos
python test_crawlee.py --videos-only

# Test only photos
python test_crawlee.py --photos-only

# Alternative: Run the module directly
python -m src.fb_crawler
```

### Force Legacy Method
If needed, you can still call the old method directly:
```python
# Force use of SeleniumBase (not recommended)
fb_data = scraper.fetch_facebook_data()
```

## Scraping Strategy

### 1. Videos Page (Primary)
- URL: `https://m.facebook.com/CACCDogs/videos/`
- Most reliable source for animal IDs
- Scrolls through video feed
- Extracts IDs from video descriptions
- Success indicators: Container-based matching

### 2. Photo Album (Secondary)
- URL: `https://m.facebook.com/CACCDogs/photos/`
- Navigates to photo viewer overlay
- Uses arrow key navigation (ArrowRight)
- Extracts IDs from photo captions
- Stops after 150 photos or loop detection

### 3. Main Feed (Backup)
- Currently not implemented in Crawlee version
- Can be added if needed

## Configuration

### Crawler Settings
```python
crawler = CACCFacebookCrawler(
    headless=True,          # Run in headless mode (GitHub Actions)
    max_requests=100        # Limit requests (prevents infinite loops)
)
```

### Playwright Crawler Settings
```python
PlaywrightCrawler(
    headless=self.headless,
    browser_type='chromium',
    max_requests_per_crawl=50,      # Videos: 50 requests
    request_handler_timeout=60,      # 60 second timeout
)
```

## Error Handling

### Popup Dismissal
Automatically dismisses:
- Login prompts ("Log In", "Sign Up")
- Cookie banners
- "See More" overlays

### Timeout Protection
- Request timeout: 60 seconds
- Page load timeout: 30 seconds
- Navigation timeout: 30 seconds

### Graceful Degradation
```python
try:
    # Try Crawlee first
    results = await crawler.scrape_all_sources()
except Exception as e:
    # Fall back to SeleniumBase
    results = self.fetch_facebook_data()
```

## Debugging

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Browser (Non-Headless)
```python
crawler = CACCFacebookCrawler(headless=False)
results = await crawler.scrape_all_sources()
```

### Check Results
```python
results = await scraper.fetch_facebook_data_crawlee()
print(f"Found {len(results)} IDs")
for dog_id, url in list(results.items())[:5]:
    print(f"{dog_id}: {url}")
```

## Performance Metrics

### Expected Results
- **Videos**: 5-15 IDs per run
- **Photos**: 20-50 IDs per run (if not blocked)
- **Total**: 25-65 IDs per full scrape
- **Success Rate**: >80% (vs 20% with SeleniumBase)

### Timing
- Videos: ~60-90 seconds
- Photos: ~120-180 seconds (depends on album size)
- Total: ~3-5 minutes per full scrape

## Troubleshooting

### Issue: No results from photos
**Cause**: Login wall or photo album URL changed
**Solution**: Check `FB_PHOTOS_URL` in `fb_crawler.py`

### Issue: Crawlee import error
**Cause**: Playwright not installed
**Solution**: Run `playwright install chromium`

### Issue: GitHub Actions failure
**Cause**: Playwright dependencies missing
**Solution**: Check workflow includes `playwright install-deps chromium`

### Issue: All IDs point to same URL
**Cause**: DOM traversal going too far up the tree
**Solution**: Adjust `max_depth` in `_extract_video_ids()` (line 1677)

## Migration Checklist

- [x] Install Crawlee: `pip install crawlee[playwright]`
- [x] Install Playwright browsers: `playwright install chromium`
- [x] Update requirements.txt
- [x] Update GitHub Actions workflows (both main and facebook-only)
- [x] Create `src/fb_crawler.py`
- [x] Update `src/scraper.py` with new async method
- [x] Update `main.py` to call new async method
- [x] Update `run_facebook_only()` to use Crawlee
- [x] Create test script: `test_crawlee.py`
- [ ] Test locally: `python test_crawlee.py`
- [ ] Test full pipeline: `python main.py`
- [ ] Commit and push changes
- [ ] Monitor GitHub Actions run
- [ ] Verify results in `dogs_active.csv`

## Rollback Plan

If Crawlee causes issues, you can rollback:

1. **Revert main.py** to use old method:
```python
fb_data = await asyncio.to_thread(scraper.fetch_facebook_data)
```

2. **Or disable Facebook scraping entirely**:
```python
fb_data = {}  # Empty dict, no Facebook links
```

3. **Or use existing data**:
```bash
python main.py --skip-scrape
```

## Future Enhancements

### Potential Improvements
1. **Proxy Rotation**: Add proxy support for better anti-detection
2. **Cookie Persistence**: Save/restore cookies between runs
3. **Rate Limiting**: Add delays between requests
4. **Multiple Browsers**: Rotate between Chrome, Firefox, WebKit
5. **Incremental Scraping**: Only scrape new posts since last run
6. **Retry Logic**: Exponential backoff for failed requests

### Example: Adding Proxy Support
```python
crawler = PlaywrightCrawler(
    headless=True,
    browser_type='chromium',
    proxy={
        'server': 'http://proxy.example.com:8080',
        'username': 'user',
        'password': 'pass'
    }
)
```

## References

- [Crawlee Python Docs](https://crawlee.dev/python/)
- [Playwright Python Docs](https://playwright.dev/python/)
- [Crawlee GitHub](https://github.com/apify/crawlee-python)

## Questions & Support

For issues or questions:
1. Check this migration guide
2. Review error messages in GitHub Actions logs
3. Test locally with `headless=False` to see what's happening
4. Open an issue in the GitHub repository
