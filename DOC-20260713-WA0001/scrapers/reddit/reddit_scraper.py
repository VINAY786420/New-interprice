"""Reddit scraper implementation using PRAW or direct API."""
from typing import Iterator, Dict, Any, Optional

from scrapers.common.base_scraper import BaseScraper
from app.core.config import settings
from app.core.logging import logger


class RedditScraper(BaseScraper):
    """Scraper for Reddit platform."""

    PLATFORM_NAME = "reddit"
    BASE_URL = "https://www.reddit.com"
    API_URL = "https://oauth.reddit.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Reddit OAuth
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            self._authenticate()

    def _authenticate(self):
        """Authenticate with Reddit API."""
        import base64

        auth = base64.b64encode(
            f"{settings.REDDIT_CLIENT_ID}:{settings.REDDIT_CLIENT_SECRET}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "User-Agent": settings.REDDIT_USER_AGENT,
        }

        data = {
            "grant_type": "client_credentials",
        }

        try:
            response = self.session.post(
                "https://www.reddit.com/api/v1/access_token",
                headers=headers,
                data=data
            )

            if response.status_code == 200:
                token = response.json().get("access_token")
                self.session.headers["Authorization"] = f"Bearer {token}"

        except Exception as e:
            logger.error("Reddit authentication failed", error=str(e))

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Reddit posts by keywords."""
        query = " OR ".join(keywords)
        subreddit = filters.get("subreddit", "all")
        sort = filters.get("sort", "relevance")
        time_period = filters.get("time", "all")
        limit = min(filters.get("limit", 100), 100)

        url = f"{self.API_URL}/r/{subreddit}/search"
        params = {
            "q": query,
            "sort": sort,
            "t": time_period,
            "limit": limit,
            "restrict_sr": "false",
        }

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})

                record = {
                    "id": post_data.get("id"),
                    "url": f"https://www.reddit.com{post_data.get('permalink')}",
                    "username": post_data.get("author"),
                    "subreddit": post_data.get("subreddit"),
                    "content": post_data.get("title", "") + "\n" + post_data.get("selftext", ""),
                    "created_at": post_data.get("created_utc"),
                    "likes_count": post_data.get("ups", 0),
                    "comments_count": post_data.get("num_comments", 0),
                    "shares_count": 0,
                    "views_count": post_data.get("upvote_ratio", 0) * post_data.get("ups", 0),
                    "is_verified": False,
                    "awards": post_data.get("total_awards_received", 0),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("Reddit search failed", error=str(e))

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Reddit user profile."""
        url = f"{self.API_URL}/user/{username}/about"

        try:
            response = self._make_request(url)
            if not response:
                return None

            data = response.json().get("data", {})

            return {
                "id": data.get("id"),
                "username": data.get("name"),
                "display_name": data.get("subreddit", {}).get("title"),
                "bio": data.get("subreddit", {}).get("public_description"),
                "karma": data.get("link_karma", 0) + data.get("comment_karma", 0),
                "created_at": data.get("created_utc"),
                "is_verified": data.get("verified", False),
                "icon_img": data.get("icon_img"),
            }

        except Exception as e:
            logger.error("Reddit profile fetch failed", error=str(e), username=username)
            return None

    def get_posts(self, username: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get Reddit posts for a user."""
        url = f"{self.API_URL}/user/{username}/submitted"
        params = {"limit": min(limit, 100)}

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})

                record = {
                    "id": post_data.get("id"),
                    "url": f"https://www.reddit.com{post_data.get('permalink')}",
                    "username": username,
                    "subreddit": post_data.get("subreddit"),
                    "content": post_data.get("title", "") + "\n" + post_data.get("selftext", ""),
                    "created_at": post_data.get("created_utc"),
                    "likes_count": post_data.get("ups", 0),
                    "comments_count": post_data.get("num_comments", 0),
                }

                yield self.normalize_record(record)

        except Exception as e:
            logger.error("Reddit posts fetch failed", error=str(e), username=username)
