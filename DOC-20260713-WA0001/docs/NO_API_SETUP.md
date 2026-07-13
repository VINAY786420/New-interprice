# 🚀 No-API Setup Guide

## Bina API Key Ke Data Collection

Is project mein **5 platforms** ke liye **no-API scrapers** included hain:

| Platform | Method | API Key Needed? |
|----------|--------|----------------|
| **Twitter/X** | Nitter instances | ❌ No |
| **Instagram** | Web scraping (sharedData) | ❌ No |
| **Reddit** | Public JSON endpoints | ❌ No |
| **YouTube** | Innertube internal API | ❌ No |
| **LinkedIn** | Requires auth cookie | ⚠️ Partial |

## Quick Start (No API Keys)

```bash
# 1. Clone repo
git clone <your-repo>
cd social-data-vault

# 2. Setup environment (NO API keys needed!)
cp .env.example .env
# Just keep default values - no changes needed

# 3. Start services
docker-compose up -d

# 4. Test scrapers
python scripts/test_scrapers.py
```

## How No-API Scrapers Work

### 1. Twitter/X → Nitter
```python
from scrapers import get_scraper

scraper = get_scraper("twitter", prefer_api=False)
for tweet in scraper.search(["#marketing"]):
    print(tweet["username"], tweet["post_content"])
```
- Uses public Nitter instances
- No Twitter API key needed
- May need proxy rotation for scale

### 2. Instagram → Web Scraping
```python
scraper = get_scraper("instagram", prefer_api=False)
for post in scraper.search(["#fitness"]):
    print(post["username"], post["likes_count"])
```
- Extracts `window._sharedData` from HTML
- Works for public profiles/hashtags
- Private accounts = blocked

### 3. Reddit → JSON Endpoints
```python
scraper = get_scraper("reddit", prefer_api=False)
for post in scraper.search(["technology"], subreddit="all"):
    print(post["username"], post["likes_count"])
```
- Just add `.json` to any Reddit URL
- 100% public, no auth needed
- Very reliable

### 4. YouTube → Innertube
```python
scraper = get_scraper("youtube", prefer_api=False)
for video in scraper.search(["python tutorial"]):
    print(video["username"], video["views_count"])
```
- Uses YouTube's internal API
- Extracted from homepage HTML
- No API key needed

## ⚠️ Important Notes

### Rate Limiting
- No-API scrapers are **slower** (2-10 sec delay)
- Use **proxy rotation** for scale
- Respect `robots.txt`

### Reliability
- Nitter instances come/go → auto-rotation built-in
- Instagram blocks IPs → use residential proxies
- YouTube changes → auto-updates via homepage fetch

### Legal
- Only scrape **publicly visible** data
- Don't bypass login walls
- Respect platform ToS
- Add delay between requests

## Proxy Setup (Recommended for Scale)

```bash
# Add to .env
PROXY_API_KEY=your-brightdata-key
PROXY_POOL_SIZE=100
```

Or use free proxies (development only):
```python
# Already included in proxy_service.py
# Auto-fallback to free proxy list
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Rate limited" | Increase delay, use proxies |
| "Nitter down" | Auto-rotates to next instance |
| "Instagram blocks" | Use residential proxy |
| "No results" | Check if content is public |

## Monetization Without API Costs

Since no API keys = **zero API costs**, your margins are higher:

| Product | Cost | Sale Price | Margin |
|---------|------|-----------|--------|
| B2B Leads | ₹0 (scraped) | ₹2-5/lead | 100% |
| Sentiment Data | ₹0 (scraped) | ₹50K-3L | 100% |
| Trend Reports | ₹0 (scraped) | ₹25K-1L | 100% |

**Only costs:** Server + Proxy + Your time
