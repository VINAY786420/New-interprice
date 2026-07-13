"""YouTube scraper implementation."""
from typing import Iterator, Dict, Any, Optional

from scrapers.common.base_scraper import BaseScraper
from app.core.config import settings
from app.core.logging import logger


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube platform."""

    PLATFORM_NAME = "youtube"
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = settings.YOUTUBE_API_KEY

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search YouTube videos by keywords."""
        if not self.api_key:
            logger.error("YouTube API key not configured")
            return iter([])

        query = " ".join(keywords)
        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(filters.get("limit", 50), 50),
            "order": filters.get("sort", "relevance"),
            "key": self.api_key,
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return iter([])

            data = response.json()
            items = data.get("items", [])

            for item in items:
                snippet = item.get("snippet", {})

                record = {
                    "id": item.get("id", {}).get("videoId"),
                    "url": f"https://youtube.com/watch?v={item.get('id', {}).get('videoId')}",
                    "username": snippet.get("channelTitle"),
                    "channel_id": snippet.get("channelId"),
                    "content": snippet.get("title", "") + "\n" + snippet.get("description", ""),
                    "created_at": snippet.get("publishedAt"),
                    "language": snippet.get("defaultLanguage"),
                    "thumbnails": snippet.get("thumbnails"),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("YouTube search failed", error=str(e))

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get YouTube channel info."""
        if not self.api_key:
            return None

        url = f"{self.BASE_URL}/channels"
        params = {
            "part": "snippet,statistics",
            "forUsername": username,
            "key": self.api_key,
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return None

            data = response.json()
            items = data.get("items", [])

            if not items:
                return None

            channel = items[0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})

            return {
                "id": channel.get("id"),
                "username": username,
                "display_name": snippet.get("title"),
                "bio": snippet.get("description"),
                "followers_count": int(stats.get("subscriberCount", 0)),
                "posts_count": int(stats.get("videoCount", 0)),
                "views_count": int(stats.get("viewCount", 0)),
                "created_at": snippet.get("publishedAt"),
                "country": snippet.get("country"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            }

        except Exception as e:
            logger.error("YouTube profile fetch failed", error=str(e), username=username)
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get YouTube videos for a channel."""
        # Get channel ID first
        profile = self.get_profile(username)
        if not profile:
            return iter([])

        channel_id = profile.get("id")

        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "maxResults": min(limit, 50),
            "order": "date",
            "key": self.api_key,
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return iter([])

            data = response.json()
            items = data.get("items", [])

            for item in items:
                snippet = item.get("snippet", {})

                record = {
                    "id": item.get("id", {}).get("videoId"),
                    "url": f"https://youtube.com/watch?v={item.get('id', {}).get('videoId')}",
                    "username": username,
                    "display_name": profile.get("display_name"),
                    "content": snippet.get("title", "") + "\n" + snippet.get("description", ""),
                    "created_at": snippet.get("publishedAt"),
                    "thumbnails": snippet.get("thumbnails"),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("YouTube posts fetch failed", error=str(e), username=username)
