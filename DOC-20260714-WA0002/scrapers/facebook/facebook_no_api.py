"""Facebook scraper WITHOUT official API - using public pages & search.

Techniques:
1. Public page scraping via m.facebook.com (mobile site - lighter, less JS)
2. Facebook search results scraping
3. Public group posts (if accessible)

WARNING: Facebook aggressively blocks scraping. Residential proxies strongly recommended.
"""
from typing import Iterator, Dict, Any, Optional, List
import re
import json
import time
import random
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class FacebookNoAPIScraper(NoAPIScraper):
    """Facebook scraper without official API keys."""

    PLATFORM_NAME = "facebook"
    BASE_URL = "https://www.facebook.com"
    MOBILE_URL = "https://m.facebook.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 5
        self.max_delay = 15
        # Facebook requires very realistic headers
        self.session.headers.update({
            "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Facebook public posts by keywords."""
        query = " ".join(keywords)

        # Use Facebook's public search
        search_url = f"{self.MOBILE_URL}/search/posts"
        params = {
            "q": query,
            "source": "filter",
            "isTrending": "0",
        }

        try:
            response = self._make_request(search_url, params=params)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract posts from search results
            posts = soup.find_all("div", role="article")

            for post in posts:
                record = self._parse_post(post)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Facebook search failed: {e}")

    def _parse_post(self, post_element) -> Optional[Dict[str, Any]]:
        """Parse a Facebook post element."""
        try:
            # Extract author
            author_elem = post_element.find("a", href=re.compile(r"^/[^/]+/$"))
            author = author_elem.text.strip() if author_elem else "Unknown"
            author_link = author_elem["href"] if author_elem else None

            # Extract content
            content_elem = post_element.find("div", {"data-ad-preview": "message"})
            if not content_elem:
                content_elem = post_element.find("span", dir="auto")
            content = content_elem.get_text(strip=True) if content_elem else ""

            # Extract timestamp
            time_elem = post_element.find("abbr")
            timestamp = None
            if time_elem and "data-utime" in time_elem.attrs:
                timestamp = datetime.fromtimestamp(int(time_elem["data-utime"]))

            # Extract engagement
            engagement_elem = post_element.find("div", string=re.compile(r"(likes|comments|shares)"))
            likes = comments = shares = 0
            if engagement_elem:
                text = engagement_elem.get_text()
                likes_match = re.search(r"([\d,.]+[KMB]?)\s*likes?", text, re.I)
                comments_match = re.search(r"([\d,.]+[KMB]?)\s*comments?", text, re.I)
                shares_match = re.search(r"([\d,.]+[KMB]?)\s*shares?", text, re.I)

                likes = self._parse_number(likes_match.group(1)) if likes_match else 0
                comments = self._parse_number(comments_match.group(1)) if comments_match else 0
                shares = self._parse_number(shares_match.group(1)) if shares_match else 0

            # Extract post URL
            post_link = post_element.find("a", href=re.compile(r"/posts/|/photos/|/videos/"))
            post_url = f"{self.BASE_URL}{post_link['href']}" if post_link else None

            return {
                "platform": "facebook",
                "source_id": None,
                "source_url": post_url,
                "username": author,
                "display_name": author,
                "post_content": content,
                "posted_at": timestamp,
                "likes_count": likes,
                "comments_count": comments,
                "shares_count": shares,
                "raw_data": {"html": str(post_element)},
            }

        except Exception as e:
            logger.error(f"Facebook post parse error: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """Parse numbers with K/M/B suffixes."""
        text = str(text).replace(",", "").strip().upper()

        multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}

        for suffix, mult in multipliers.items():
            if suffix in text:
                try:
                    return int(float(text.replace(suffix, "")) * mult)
                except:
                    return 0

        try:
            return int(text)
        except:
            return 0

    def get_page_posts(self, page_name: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get posts from a public Facebook page."""
        url = f"{self.MOBILE_URL}/{page_name}"

        try:
            response = self._make_request(url)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            posts = soup.find_all("div", role="article")

            count = 0
            for post in posts:
                if count >= limit:
                    break

                record = self._parse_post(post)
                if record:
                    record["username"] = page_name
                    yield record
                    count += 1

        except Exception as e:
            logger.error(f"Facebook page fetch failed: {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Facebook public profile info."""
        url = f"{self.MOBILE_URL}/{username}"

        try:
            response = self._make_request(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract profile info
            name_elem = soup.find("h1") or soup.find("title")
            name = name_elem.text.strip() if name_elem else username

            # Extract follower count
            follower_text = soup.find(string=re.compile(r"([\d,.]+[KMB]?)\s*(followers|people follow)"))
            followers = 0
            if follower_text:
                match = re.search(r"([\d,.]+[KMB]?)", str(follower_text))
                if match:
                    followers = self._parse_number(match.group(1))

            # Extract bio/about
            bio_elem = soup.find("div", string=re.compile(r"About|Intro"))
            bio = bio_elem.find_next("div").get_text(strip=True) if bio_elem else ""

            return {
                "platform": "facebook",
                "username": username,
                "display_name": name,
                "bio": bio,
                "followers_count": followers,
                "following_count": 0,
                "posts_count": 0,
                "is_verified": False,
                "raw_data": {"html": response.text[:5000]},
            }

        except Exception as e:
            logger.error(f"Facebook profile fetch failed: {e}")
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get posts for a Facebook user/page."""
        yield from self.get_page_posts(username, limit)
