"""Reddit scraper WITHOUT official API - using JSON endpoints.

Reddit provides public JSON endpoints for all public content.
Simply add '.json' to any Reddit URL to get structured data.

Example:
- https://www.reddit.com/r/technology.json
- https://www.reddit.com/user/spez.json
- https://www.reddit.com/r/technology/comments/abc123.json
"""
from typing import Iterator, Dict, Any, Optional
import re
from datetime import datetime

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class RedditNoAPIScraper(NoAPIScraper):
    """Reddit scraper using public JSON endpoints (NO API key needed)."""

    PLATFORM_NAME = "reddit"
    BASE_URL = "https://www.reddit.com"
    JSON_URL = "https://www.reddit.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 2
        self.max_delay = 5
        # Reddit requires a User-Agent
        self.session.headers.update({
            "User-Agent": "SocialDataVault/1.0 (Educational Research Bot)",
        })

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Reddit posts using JSON endpoints."""
        subreddit = filters.get("subreddit", "all")
        sort = filters.get("sort", "relevance")
        time_period = filters.get("time", "all")
        limit = min(filters.get("limit", 100), 100)

        query = "+".join(keywords)

        # Build search URL
        url = f"{self.JSON_URL}/r/{subreddit}/search.json"
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
                record = self._parse_post(post_data)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Reddit search failed: {e}")

    def _parse_post(self, post_data: dict) -> Optional[Dict[str, Any]]:
        """Parse a Reddit post into standard format."""
        try:
            created_utc = post_data.get("created_utc", 0)

            return {
                "platform": "reddit",
                "source_id": post_data.get("id"),
                "source_url": f"https://www.reddit.com{post_data.get('permalink', '')}",
                "username": post_data.get("author"),
                "display_name": post_data.get("author"),
                "post_content": post_data.get("title", "") + "\n" + post_data.get("selftext", ""),
                "posted_at": datetime.fromtimestamp(created_utc) if created_utc else None,
                "likes_count": post_data.get("ups", 0),
                "comments_count": post_data.get("num_comments", 0),
                "shares_count": 0,
                "views_count": int(post_data.get("upvote_ratio", 0) * post_data.get("ups", 0)),
                "subreddit": post_data.get("subreddit"),
                "is_verified": False,
                "awards": post_data.get("total_awards_received", 0),
                "is_nsfw": post_data.get("over_18", False),
                "is_spoiler": post_data.get("spoiler", False),
                "url": post_data.get("url"),
                "domain": post_data.get("domain"),
                "raw_data": post_data,
            }

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Reddit user profile via JSON endpoint."""
        url = f"{self.JSON_URL}/user/{username}/about.json"

        try:
            response = self._make_request(url)
            if not response:
                return None

            data = response.json()
            user_data = data.get("data", {})

            created_utc = user_data.get("created_utc", 0)

            return {
                "id": user_data.get("id"),
                "username": user_data.get("name"),
                "display_name": user_data.get("subreddit", {}).get("title", username),
                "bio": user_data.get("subreddit", {}).get("public_description", ""),
                "karma": user_data.get("link_karma", 0) + user_data.get("comment_karma", 0),
                "link_karma": user_data.get("link_karma", 0),
                "comment_karma": user_data.get("comment_karma", 0),
                "created_at": datetime.fromtimestamp(created_utc) if created_utc else None,
                "is_verified": user_data.get("verified", False),
                "is_gold": user_data.get("is_gold", False),
                "is_mod": user_data.get("is_mod", False),
                "icon_img": user_data.get("icon_img"),
                "raw_data": user_data,
            }

        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            return None

    def get_posts(self, username: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get Reddit posts for a user."""
        url = f"{self.JSON_URL}/user/{username}/submitted.json"
        params = {"limit": min(limit, 100)}

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})
                record = self._parse_post(post_data)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Posts fetch failed: {e}")

    def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get posts from a subreddit."""
        url = f"{self.JSON_URL}/r/{subreddit}/{sort}.json"
        params = {"limit": min(limit, 100)}

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})
                record = self._parse_post(post_data)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Subreddit fetch failed: {e}")

    def get_comments(self, post_id: str, subreddit: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get comments for a post."""
        url = f"{self.JSON_URL}/r/{subreddit}/comments/{post_id}.json"
        params = {"limit": min(limit, 100)}

        try:
            response = self._make_request(url, params=params)
            if not response:
                return

            data = response.json()
            if len(data) > 1:
                comments = data[1].get("data", {}).get("children", [])

                for comment in comments:
                    comment_data = comment.get("data", {})

                    if comment_data.get("body"):
                        created_utc = comment_data.get("created_utc", 0)

                        yield {
                            "platform": "reddit",
                            "source_id": comment_data.get("id"),
                            "source_url": f"https://www.reddit.com{comment_data.get('permalink', '')}",
                            "username": comment_data.get("author"),
                            "post_content": comment_data.get("body", ""),
                            "posted_at": datetime.fromtimestamp(created_utc) if created_utc else None,
                            "likes_count": comment_data.get("ups", 0),
                            "is_verified": False,
                            "parent_id": comment_data.get("parent_id"),
                            "depth": comment_data.get("depth", 0),
                            "raw_data": comment_data,
                        }

        except Exception as e:
            logger.error(f"Comments fetch failed: {e}")
