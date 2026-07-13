"""Twitter/X scraper implementation."""
from typing import Iterator, Dict, Any, Optional
import json

from scrapers.common.base_scraper import BaseScraper
from app.core.config import settings
from app.core.logging import logger


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X platform."""

    PLATFORM_NAME = "twitter"
    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set up Twitter API authentication
        if settings.TWITTER_BEARER_TOKEN:
            self.session.headers["Authorization"] = f"Bearer {settings.TWITTER_BEARER_TOKEN}"

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search tweets by keywords."""
        query = " OR ".join(keywords)

        # Add filters
        if filters.get("min_retweets"):
            query += f" min_retweets:{filters['min_retweets']}"
        if filters.get("lang"):
            query += f" lang:{filters['lang']}"

        url = f"{self.BASE_URL}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(filters.get("limit", 100), 100),
            "tweet.fields": "created_at,public_metrics,context_annotations,lang,source",
            "user.fields": "username,public_metrics,verified,description,location",
            "expansions": "author_id",
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            for tweet in tweets:
                author = users.get(tweet.get("author_id"), {})
                metrics = tweet.get("public_metrics", {})

                record = {
                    "id": tweet.get("id"),
                    "url": f"https://twitter.com/i/web/status/{tweet.get('id')}",
                    "username": author.get("username"),
                    "display_name": author.get("name"),
                    "content": tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "language": tweet.get("lang"),
                    "followers_count": author.get("public_metrics", {}).get("followers_count", 0),
                    "following_count": author.get("public_metrics", {}).get("following_count", 0),
                    "posts_count": author.get("public_metrics", {}).get("tweet_count", 0),
                    "likes_count": metrics.get("like_count", 0),
                    "comments_count": metrics.get("reply_count", 0),
                    "shares_count": metrics.get("retweet_count", 0),
                    "views_count": metrics.get("impression_count", 0),
                    "is_verified": author.get("verified", False),
                    "country": author.get("location"),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("Twitter search failed", error=str(e))

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Twitter profile by username."""
        url = f"{self.BASE_URL}/users/by/username/{username}"
        params = {
            "user.fields": "created_at,description,public_metrics,verified,location,url",
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return None

            data = response.json().get("data", {})
            metrics = data.get("public_metrics", {})

            return {
                "id": data.get("id"),
                "username": data.get("username"),
                "display_name": data.get("name"),
                "bio": data.get("description"),
                "followers_count": metrics.get("followers_count", 0),
                "following_count": metrics.get("following_count", 0),
                "posts_count": metrics.get("tweet_count", 0),
                "is_verified": data.get("verified", False),
                "location": data.get("location"),
                "url": data.get("url"),
                "created_at": data.get("created_at"),
            }

        except Exception as e:
            logger.error("Twitter profile fetch failed", error=str(e), username=username)
            return None

    def get_posts(self, username: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get tweets for a user."""
        # First get user ID
        profile = self.get_profile(username)
        if not profile:
            return

        user_id = profile["id"]
        url = f"{self.BASE_URL}/users/{user_id}/tweets"
        params = {
            "max_results": min(limit, 100),
            "tweet.fields": "created_at,public_metrics,context_annotations,lang",
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            tweets = data.get("data", [])

            for tweet in tweets:
                metrics = tweet.get("public_metrics", {})

                record = {
                    "id": tweet.get("id"),
                    "url": f"https://twitter.com/{username}/status/{tweet.get('id')}",
                    "username": username,
                    "display_name": profile.get("display_name"),
                    "content": tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "language": tweet.get("lang"),
                    "likes_count": metrics.get("like_count", 0),
                    "comments_count": metrics.get("reply_count", 0),
                    "shares_count": metrics.get("retweet_count", 0),
                    "views_count": metrics.get("impression_count", 0),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("Twitter posts fetch failed", error=str(e), username=username)
