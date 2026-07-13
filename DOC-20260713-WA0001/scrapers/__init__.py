"""Unified scraper factory - automatically selects API or no-API version."""
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger


def get_scraper(platform: str, prefer_api: bool = True):
    """Get the best available scraper for a platform.

    Args:
        platform: Platform name (twitter, instagram, reddit, youtube, linkedin)
        prefer_api: If True, try API version first, fallback to no-API

    Returns:
        Scraper instance
    """
    platform = platform.lower()

    scraper_map = {
        "twitter": _get_twitter_scraper,
        "instagram": _get_instagram_scraper,
        "reddit": _get_reddit_scraper,
        "youtube": _get_youtube_scraper,
        "linkedin": _get_linkedin_scraper,
    }

    if platform not in scraper_map:
        raise ValueError(f"Unknown platform: {platform}")

    return scraper_map[platform](prefer_api)


def _get_twitter_scraper(prefer_api: bool):
    """Get Twitter scraper."""
    if prefer_api and settings.TWITTER_BEARER_TOKEN:
        from scrapers.twitter.twitter_scraper import TwitterScraper
        logger.info("Using Twitter API scraper")
        return TwitterScraper()
    else:
        from scrapers.twitter.twitter_no_api import TwitterNoAPIScraper
        logger.info("Using Twitter no-API scraper (Nitter)")
        return TwitterNoAPIScraper()


def _get_instagram_scraper(prefer_api: bool):
    """Get Instagram scraper."""
    if prefer_api and settings.INSTAGRAM_ACCESS_TOKEN:
        from scrapers.instagram.instagram_scraper import InstagramScraper
        logger.info("Using Instagram API scraper")
        return InstagramScraper()
    else:
        from scrapers.instagram.instagram_no_api import InstagramNoAPIScraper
        logger.info("Using Instagram no-API scraper")
        return InstagramNoAPIScraper()


def _get_reddit_scraper(prefer_api: bool):
    """Get Reddit scraper."""
    if prefer_api and settings.REDDIT_CLIENT_ID:
        from scrapers.reddit.reddit_scraper import RedditScraper
        logger.info("Using Reddit API scraper")
        return RedditScraper()
    else:
        from scrapers.reddit.reddit_no_api import RedditNoAPIScraper
        logger.info("Using Reddit no-API scraper (JSON endpoints)")
        return RedditNoAPIScraper()


def _get_youtube_scraper(prefer_api: bool):
    """Get YouTube scraper."""
    if prefer_api and settings.YOUTUBE_API_KEY:
        from scrapers.youtube.youtube_scraper import YouTubeScraper
        logger.info("Using YouTube API scraper")
        return YouTubeScraper()
    else:
        from scrapers.youtube.youtube_no_api import YouTubeNoAPIScraper
        logger.info("Using YouTube no-API scraper (Innertube)")
        return YouTubeNoAPIScraper()


def _get_linkedin_scraper(prefer_api: bool):
    """Get LinkedIn scraper."""
    if prefer_api and settings.LINKEDIN_ACCESS_TOKEN:
        from scrapers.linkedin.linkedin_scraper import LinkedInScraper
        logger.info("Using LinkedIn API scraper")
        return LinkedInScraper()
    else:
        from scrapers.linkedin.linkedin_no_api import LinkedInNoAPIScraper
        logger.info("Using LinkedIn no-API scraper (requires auth cookie)")
        return LinkedInNoAPIScraper()


def get_all_scrapers() -> Dict[str, Any]:
    """Get all available scrapers."""
    platforms = ["twitter", "instagram", "reddit", "youtube", "linkedin"]
    scrapers = {}

    for platform in platforms:
        try:
            scrapers[platform] = get_scraper(platform, prefer_api=False)
        except Exception as e:
            logger.warning(f"Could not initialize scraper for {platform}: {e}")

    return scrapers
