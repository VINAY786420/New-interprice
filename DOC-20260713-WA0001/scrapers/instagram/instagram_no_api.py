"""Instagram scraper WITHOUT official API - using web scraping.

Uses multiple techniques:
1. Public profile pages (no login required)
2. Instagram's internal GraphQL endpoints
3. embed.instagram.com for public posts
"""
from typing import Iterator, Dict, Any, Optional
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class InstagramNoAPIScraper(NoAPIScraper):
    """Instagram scraper without official API."""

    PLATFORM_NAME = "instagram"
    BASE_URL = "https://www.instagram.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 4
        self.max_delay = 12
        self._csrf_token = None
        self._session_id = None

    def _get_shared_data(self, html: str) -> Optional[dict]:
        """Extract sharedData JSON from Instagram HTML."""
        patterns = [
            r'<script type="text/javascript">window\._sharedData = ({.*?});</script>',
            r'window\._sharedData = ({.*?});',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        return None

    def _get_additional_data(self, html: str) -> Optional[dict]:
        """Extract additional data from Instagram."""
        match = re.search(r'<script type="application/json" data-sjs>(.*?)</script>', html)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return None

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Instagram by hashtags (public data only)."""
        for keyword in keywords:
            hashtag = keyword.lstrip("#")
            yield from self._scrape_hashtag(hashtag, **filters)

    def _scrape_hashtag(self, hashtag: str, **filters) -> Iterator[Dict[str, Any]]:
        """Scrape posts from a hashtag page."""
        url = f"{self.BASE_URL}/explore/tags/{hashtag}/"

        try:
            response = self._make_request(url)
            if not response:
                return

            html = response.text
            shared_data = self._get_shared_data(html)

            if not shared_data:
                logger.warning(f"Could not extract shared data for #{hashtag}")
                return

            # Extract hashtag data
            tag_page = shared_data.get("entry_data", {}).get("TagPage", [{}])[0]
            graphql = tag_page.get("graphql", {}).get("hashtag", {})
            edges = graphql.get("edge_hashtag_to_media", {}).get("edges", [])

            for edge in edges:
                node = edge.get("node", {})

                # Extract caption
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""

                record = {
                    "platform": "instagram",
                    "source_id": node.get("id"),
                    "source_url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                    "username": None,  # Need additional request
                    "post_content": caption,
                    "posted_at": datetime.fromtimestamp(node.get("taken_at_timestamp", 0)),
                    "likes_count": node.get("edge_liked_by", {}).get("count", 0),
                    "comments_count": node.get("edge_media_to_comment", {}).get("count", 0),
                    "is_video": node.get("is_video", False),
                    "media_url": node.get("display_url"),
                    "dimensions": node.get("dimensions"),
                    "hashtags": re.findall(r'#(\w+)', caption),
                    "mentions": re.findall(r'@(\w+)', caption),
                    "raw_data": node,
                }

                yield record

        except Exception as e:
            logger.error(f"Hashtag scrape failed: {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Instagram profile (public data only)."""
        url = f"{self.BASE_URL}/{username}/"

        try:
            response = self._make_request(url)
            if not response:
                return None

            html = response.text
            shared_data = self._get_shared_data(html)

            if not shared_data:
                return None

            user = shared_data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})

            if not user:
                return None

            return {
                "id": user.get("id"),
                "username": user.get("username"),
                "display_name": user.get("full_name"),
                "bio": user.get("biography"),
                "followers_count": user.get("edge_followed_by", {}).get("count", 0),
                "following_count": user.get("edge_follow", {}).get("count", 0),
                "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
                "is_verified": user.get("is_verified", False),
                "is_business_account": user.get("is_business_account", False),
                "is_private": user.get("is_private", False),
                "profile_pic_url": user.get("profile_pic_url"),
                "external_url": user.get("external_url"),
                "category": user.get("category_name"),
                "raw_data": user,
            }

        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get Instagram posts for a user."""
        profile = self.get_profile(username)
        if not profile or profile.get("is_private"):
            logger.warning(f"Profile private or not found: {username}")
            return

        url = f"{self.BASE_URL}/{username}/"

        try:
            response = self._make_request(url)
            if not response:
                return

            html = response.text
            shared_data = self._get_shared_data(html)

            if not shared_data:
                return

            user = shared_data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})
            edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])[:limit]

            for edge in edges:
                node = edge.get("node", {})

                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""

                record = {
                    "platform": "instagram",
                    "source_id": node.get("id"),
                    "source_url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                    "username": username,
                    "display_name": profile.get("display_name"),
                    "post_content": caption,
                    "posted_at": datetime.fromtimestamp(node.get("taken_at_timestamp", 0)),
                    "likes_count": node.get("edge_liked_by", {}).get("count", 0),
                    "comments_count": node.get("edge_media_to_comment", {}).get("count", 0),
                    "is_video": node.get("is_video", False),
                    "media_url": node.get("display_url"),
                    "hashtags": re.findall(r'#(\w+)', caption),
                    "mentions": re.findall(r'@(\w+)', caption),
                    "raw_data": node,
                }

                yield record

        except Exception as e:
            logger.error(f"Posts fetch failed: {e}")

    def get_post_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Get a single post by shortcode (works for public posts)."""
        url = f"{self.BASE_URL}/p/{shortcode}/"

        try:
            response = self._make_request(url)
            if not response:
                return None

            html = response.text
            shared_data = self._get_shared_data(html)

            if not shared_data:
                return None

            post = shared_data.get("entry_data", {}).get("PostPage", [{}])[0].get("graphql", {}).get("shortcode_media", {})

            if not post:
                return None

            owner = post.get("owner", {})
            caption_edges = post.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""

            return {
                "platform": "instagram",
                "source_id": post.get("id"),
                "source_url": f"https://www.instagram.com/p/{shortcode}/",
                "username": owner.get("username"),
                "display_name": owner.get("full_name"),
                "post_content": caption,
                "posted_at": datetime.fromtimestamp(post.get("taken_at_timestamp", 0)),
                "likes_count": post.get("edge_media_preview_like", {}).get("count", 0),
                "comments_count": post.get("edge_media_to_parent_comment", {}).get("count", 0),
                "is_video": post.get("is_video", False),
                "media_url": post.get("display_url"),
                "hashtags": re.findall(r'#(\w+)', caption),
                "mentions": re.findall(r'@(\w+)', caption),
                "raw_data": post,
            }

        except Exception as e:
            logger.error(f"Post fetch failed: {e}")
            return None
