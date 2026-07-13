"""Instagram scraper implementation."""
from typing import Iterator, Dict, Any, Optional
import re

from scrapers.common.base_scraper import BaseScraper
from app.core.logging import logger


class InstagramScraper(BaseScraper):
    """Scraper for Instagram platform."""

    PLATFORM_NAME = "instagram"
    BASE_URL = "https://www.instagram.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session.headers.update({
            "X-IG-App-ID": "936619743392459",  # Instagram web app ID
        })

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Instagram posts by hashtags."""
        for keyword in keywords:
            hashtag = keyword.lstrip("#")
            yield from self._search_hashtag(hashtag, **filters)

    def _search_hashtag(self, hashtag: str, **filters) -> Iterator[Dict[str, Any]]:
        """Search posts by hashtag."""
        url = f"{self.BASE_URL}/explore/tags/{hashtag}/"

        try:
            response = self._make_request(url)
            if not response:
                return

            # Extract shared data from page
            html = response.text
            match = re.search(r'<script type="text/javascript">window._sharedData = ({.*?});</script>', html)

            if match:
                data = json.loads(match.group(1))
                posts = data.get("entry_data", {}).get("TagPage", [{}])[0].get("graphql", {}).get("hashtag", {}).get("edge_hashtag_to_media", {}).get("edges", [])

                for edge in posts:
                    node = edge.get("node", {})

                    record = {
                        "id": node.get("id"),
                        "url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                        "username": node.get("owner", {}).get("username"),
                        "content": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
                        "created_at": node.get("taken_at_timestamp"),
                        "likes_count": node.get("edge_liked_by", {}).get("count", 0),
                        "comments_count": node.get("edge_media_to_comment", {}).get("count", 0),
                        "is_video": node.get("is_video", False),
                        "media_url": node.get("display_url"),
                    }

                    yield self.normalize_record(record)

        except Exception as e:
            logger.error("Instagram hashtag search failed", error=str(e), hashtag=hashtag)

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Instagram profile."""
        url = f"{self.BASE_URL}/{username}/"

        try:
            response = self._make_request(url)
            if not response:
                return None

            html = response.text
            match = re.search(r'<script type="text/javascript">window._sharedData = ({.*?});</script>', html)

            if match:
                data = json.loads(match.group(1))
                user = data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})

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
                    "profile_pic_url": user.get("profile_pic_url"),
                    "external_url": user.get("external_url"),
                }

            return None

        except Exception as e:
            logger.error("Instagram profile fetch failed", error=str(e), username=username)
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get Instagram posts for a user."""
        profile = self.get_profile(username)
        if not profile:
            return

        url = f"{self.BASE_URL}/{username}/"

        try:
            response = self._make_request(url)
            if not response:
                return

            html = response.text
            match = re.search(r'<script type="text/javascript">window._sharedData = ({.*?});</script>', html)

            if match:
                data = json.loads(match.group(1))
                user = data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})
                edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])[:limit]

                for edge in edges:
                    node = edge.get("node", {})

                    record = {
                        "id": node.get("id"),
                        "url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                        "username": username,
                        "display_name": profile.get("display_name"),
                        "content": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
                        "created_at": node.get("taken_at_timestamp"),
                        "likes_count": node.get("edge_liked_by", {}).get("count", 0),
                        "comments_count": node.get("edge_media_to_comment", {}).get("count", 0),
                        "is_video": node.get("is_video", False),
                        "media_url": node.get("display_url"),
                    }

                    yield self.normalize_record(record)

        except Exception as e:
            logger.error("Instagram posts fetch failed", error=str(e), username=username)
