"""YouTube scraper WITHOUT official API - using Innertube/WEB API.

YouTube has internal APIs that can be accessed without an API key
by mimicking the YouTube web app requests.

This uses the Innertube API which powers the YouTube web interface.
"""
from typing import Iterator, Dict, Any, Optional
import re
from datetime import datetime

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class YouTubeNoAPIScraper(NoAPIScraper):
    """YouTube scraper using internal Innertube API (NO API key needed)."""

    PLATFORM_NAME = "youtube"
    BASE_URL = "https://www.youtube.com"
    INNERTUBE_API = "https://www.youtube.com/youtubei/v1"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 3
        self.max_delay = 8
        self._api_key = None
        self._context = None
        self._visitor_data = None
        self._init_innertube()

    def _init_innertube(self):
        """Initialize Innertube API by fetching homepage."""
        try:
            response = self._make_request(self.BASE_URL)
            if not response:
                return

            html = response.text

            # Extract API key
            api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
            if api_key_match:
                self._api_key = api_key_match.group(1)

            # Extract context
            context_match = re.search(r'"INNERTUBE_CONTEXT":({[^}]+})', html)
            if context_match:
                import json
                self._context = json.loads(context_match.group(1))

            # Extract visitor data
            visitor_match = re.search(r'"visitorData":"([^"]+)"', html)
            if visitor_match:
                self._visitor_data = visitor_match.group(1)

            logger.info("Innertube initialized", api_key=bool(self._api_key))

        except Exception as e:
            logger.error(f"Innertube init failed: {e}")

    def _build_payload(self, additional_data: dict = None) -> dict:
        """Build Innertube API payload."""
        payload = {
            "context": {
                "client": {
                    "hl": "en",
                    "gl": "US",
                    "visitorData": self._visitor_data,
                    "clientName": "WEB",
                    "clientVersion": "2.20231201.01.00",
                    "osName": "Windows",
                    "osVersion": "10.0",
                    "platform": "DESKTOP",
                }
            }
        }

        if additional_data:
            payload.update(additional_data)

        return payload

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search YouTube videos using Innertube API."""
        if not self._api_key:
            logger.error("Innertube API not initialized")
            return

        query = " ".join(keywords)

        url = f"{self.INNERTUBE_API}/search"
        params = {"key": self._api_key}

        payload = self._build_payload({
            "query": query,
        })

        try:
            response = self._make_request(url, method="POST", json=payload, params=params)
            if not response:
                return

            data = response.json()

            # Extract video results
            contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])

            for section in contents:
                items = section.get("itemSectionRenderer", {}).get("contents", [])

                for item in items:
                    video = item.get("videoRenderer")
                    if video:
                        record = self._parse_video(video)
                        if record:
                            yield record

        except Exception as e:
            logger.error(f"YouTube search failed: {e}")

    def _parse_video(self, video_data: dict) -> Optional[Dict[str, Any]]:
        """Parse video data from Innertube response."""
        try:
            video_id = video_data.get("videoId")
            title = self._extract_text(video_data.get("title", {}))

            # Extract channel info
            owner_text = self._extract_text(video_data.get("ownerText", {}))

            # Extract view count
            view_count_text = self._extract_text(video_data.get("viewCountText", {}))
            views = self._parse_view_count(view_count_text)

            # Extract published time
            published_text = self._extract_text(video_data.get("publishedTimeText", {}))

            # Extract thumbnails
            thumbnails = video_data.get("thumbnail", {}).get("thumbnails", [])
            thumbnail_url = thumbnails[-1].get("url") if thumbnails else None

            # Extract length
            length_text = self._extract_text(video_data.get("lengthText", {}))

            return {
                "platform": "youtube",
                "source_id": video_id,
                "source_url": f"https://youtube.com/watch?v={video_id}",
                "username": owner_text,
                "display_name": owner_text,
                "post_content": title,
                "posted_at": None,  # Need additional parsing
                "views_count": views,
                "likes_count": 0,  # Not available in search
                "comments_count": 0,
                "duration": length_text,
                "thumbnail_url": thumbnail_url,
                "raw_data": video_data,
            }

        except Exception as e:
            logger.error(f"Video parse error: {e}")
            return None

    def _extract_text(self, text_obj: dict) -> str:
        """Extract text from Innertube text object."""
        if isinstance(text_obj, str):
            return text_obj

        runs = text_obj.get("runs", [])
        if runs:
            return "".join(run.get("text", "") for run in runs)

        return text_obj.get("simpleText", "")

    def _parse_view_count(self, text: str) -> int:
        """Parse view count from text like '1.2M views'."""
        if not text:
            return 0

        # Remove non-numeric characters except K, M, B
        match = re.search(r'([\d,.]+)([KMB]?)', text.replace(",", ""))
        if not match:
            return 0

        number = float(match.group(1))
        suffix = match.group(2)

        multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
        return int(number * multipliers.get(suffix, 1))

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get YouTube channel info."""
        # Try to get channel by username
        url = f"{self.BASE_URL}/@{username}"

        try:
            response = self._make_request(url)
            if not response:
                return None

            html = response.text

            # Extract channel data from initial data
            match = re.search(r'var ytInitialData = ({.*?});</script>', html, re.DOTALL)
            if not match:
                return None

            import json
            data = json.loads(match.group(1))

            # Extract channel info from header
            header = data.get("header", {}).get("c4TabbedHeaderRenderer", {})

            title = self._extract_text(header.get("title", {}))
            subscribers_text = self._extract_text(header.get("subscriberCountText", {}))

            # Extract avatar
            avatars = header.get("avatar", {}).get("thumbnails", [])
            avatar_url = avatars[-1].get("url") if avatars else None

            # Extract banner
            banners = header.get("banner", {}).get("thumbnails", [])
            banner_url = banners[-1].get("url") if banners else None

            return {
                "username": username,
                "display_name": title,
                "subscribers_text": subscribers_text,
                "avatar_url": avatar_url,
                "banner_url": banner_url,
                "raw_data": data,
            }

        except Exception as e:
            logger.error(f"Channel fetch failed: {e}")
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get videos from a channel."""
        # This requires channel ID - simplified implementation
        logger.warning("YouTube channel videos require channel ID - use search instead")
        return iter([])
