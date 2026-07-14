"""Unified scraper factory - 10 platforms."""
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

def get_scraper(platform: str, prefer_api: bool = True):
    platform = platform.lower()
    scraper_map = {
        "twitter": _get_twitter_scraper,
        "instagram": _get_instagram_scraper,
        "reddit": _get_reddit_scraper,
        "youtube": _get_youtube_scraper,
        "linkedin": _get_linkedin_scraper,
        "facebook": _get_facebook_scraper,
        "pinterest": _get_pinterest_scraper,
        "google_search": _get_google_search_scraper,
        "amazon": _get_amazon_scraper,
        "flipkart": _get_flipkart_scraper,
    }
    if platform not in scraper_map:
        raise ValueError(f"Unknown platform: {platform}")
    return scraper_map[platform](prefer_api)

def _get_twitter_scraper(prefer_api: bool):
    from scrapers.twitter.twitter_no_api import TwitterNoAPIScraper
    return TwitterNoAPIScraper()

def _get_instagram_scraper(prefer_api: bool):
    from scrapers.instagram.instagram_no_api import InstagramNoAPIScraper
    return InstagramNoAPIScraper()

def _get_reddit_scraper(prefer_api: bool):
    from scrapers.reddit.reddit_no_api import RedditNoAPIScraper
    return RedditNoAPIScraper()

def _get_youtube_scraper(prefer_api: bool):
    from scrapers.youtube.youtube_no_api import YouTubeNoAPIScraper
    return YouTubeNoAPIScraper()

def _get_linkedin_scraper(prefer_api: bool):
    from scrapers.linkedin.linkedin_no_api import LinkedInNoAPIScraper
    return LinkedInNoAPIScraper()

def _get_facebook_scraper(prefer_api: bool):
    from scrapers.facebook.facebook_no_api import FacebookNoAPIScraper
    return FacebookNoAPIScraper()

def _get_pinterest_scraper(prefer_api: bool):
    from scrapers.pinterest.pinterest_no_api import PinterestNoAPIScraper
    return PinterestNoAPIScraper()

def _get_google_search_scraper(prefer_api: bool):
    from scrapers.google_search.google_search_no_api import GoogleSearchNoAPIScraper
    return GoogleSearchNoAPIScraper()

def _get_amazon_scraper(prefer_api: bool):
    from scrapers.amazon.amazon_no_api import AmazonNoAPIScraper
    return AmazonNoAPIScraper()

def _get_flipkart_scraper(prefer_api: bool):
    from scrapers.flipkart.flipkart_no_api import FlipkartNoAPIScraper
    return FlipkartNoAPIScraper()

def get_all_scrapers() -> Dict[str, Any]:
    platforms = ["twitter", "instagram", "reddit", "youtube", "linkedin",
                 "facebook", "pinterest", "google_search", "amazon", "flipkart"]
    scrapers = {}
    for platform in platforms:
        try:
            scrapers[platform] = get_scraper(platform, prefer_api=False)
        except Exception as e:
            logger.warning(f"Could not initialize {platform}: {e}")
    return scrapers
