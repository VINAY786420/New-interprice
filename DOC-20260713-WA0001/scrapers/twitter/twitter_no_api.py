"""Twitter scraper WITHOUT official API - using Nitter instances.

Nitter is an open-source alternative Twitter frontend that doesn't require API keys.
This scraper uses Nitter instances to fetch public Twitter data.

Note: Nitter instances come and go. This scraper includes fallback logic.
"""
from typing import Iterator, Dict, Any, Optional, List
import re
from datetime import datetime
from bs4 import BeautifulSoup

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class TwitterNoAPIScraper(NoAPIScraper):
    """Twitter scraper without official API keys."""

    PLATFORM_NAME = "twitter"

    # Nitter instances (public, free)
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.it",
        "https://nitter.cz",
        "https://nitter.privacydev.net",
        "https://nitter.projectsegfault.com",
        "https://nitter.datura.network",
        "https://nitter.perennialte.ch",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_instance = 0
        self.min_delay = 3  # Be gentle with Nitter
        self.max_delay = 10

    def _get_nitter_url(self, path: str) -> str:
        """Get Nitter URL with instance rotation."""
        instance = self.NITTER_INSTANCES[self.current_instance % len(self.NITTER_INSTANCES)]
        return f"{instance}{path}"

    def _rotate_instance(self):
        """Rotate to next Nitter instance."""
        self.current_instance += 1
        logger.info(f"Rotating to Nitter instance: {self.NITTER_INSTANCES[self.current_instance % len(self.NITTER_INSTANCES)]}")

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search tweets using Nitter."""
        query = " ".join(keywords)

        # Build search URL
        search_params = f"?q={requests.utils.quote(query)}&f=tweets"

        if filters.get("min_likes"):
            search_params += f"&min_likes={filters['min_likes']}"
        if filters.get("lang"):
            search_params += f"&lang={filters['lang']}"

        url = self._get_nitter_url(f"/search{search_params}")

        try:
            response = self._make_request(url)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            tweets = soup.find_all("div", class_="timeline-item")

            for tweet in tweets:
                try:
                    record = self._parse_tweet(tweet)
                    if record:
                        yield record
                except Exception as e:
                    logger.error(f"Error parsing tweet: {e}")
                    continue

            # Handle pagination
            next_link = soup.find("a", class_="show-more", string="Load more")
            if next_link and filters.get("limit", 0) > len(tweets):
                # TODO: Implement pagination
                pass

        except Exception as e:
            logger.error(f"Nitter search failed: {e}")

    def _parse_tweet(self, tweet_element) -> Optional[Dict[str, Any]]:
        """Parse a single tweet element."""
        try:
            # Extract username
            username_elem = tweet_element.find("a", class_="username")
            username = username_elem.text.strip().lstrip("@") if username_elem else None

            # Extract display name
            display_name_elem = tweet_element.find("a", class_="fullname")
            display_name = display_name_elem.text.strip() if display_name_elem else username

            # Extract content
            content_elem = tweet_element.find("div", class_="tweet-content")
            content = content_elem.get_text(strip=True) if content_elem else ""

            # Extract date
            date_elem = tweet_element.find("span", class_="tweet-date")
            date_str = date_elem.find("a")["title"] if date_elem else None
            posted_at = self._parse_date(date_str) if date_str else None

            # Extract engagement
            stats = tweet_element.find("div", class_="tweet-stats")
            likes = self._extract_stat(stats, "icon-heart")
            retweets = self._extract_stat(stats, "icon-retweet")
            replies = self._extract_stat(stats, "icon-comment")

            # Extract tweet ID from link
            link_elem = tweet_element.find("a", class_="tweet-link")
            tweet_id = None
            if link_elem and "href" in link_elem.attrs:
                match = re.search(r"/status/(\d+)", link_elem["href"])
                if match:
                    tweet_id = match.group(1)

            return {
                "platform": "twitter",
                "source_id": tweet_id,
                "source_url": f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else None,
                "username": username,
                "display_name": display_name,
                "post_content": content,
                "posted_at": posted_at,
                "likes_count": likes,
                "comments_count": replies,
                "shares_count": retweets,
                "is_verified": bool(tweet_element.find("span", class_="verified-icon")),
                "raw_data": {"html": str(tweet_element)},
            }

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    def _extract_stat(self, stats_element, icon_class: str) -> int:
        """Extract numeric stat from icon class."""
        if not stats_element:
            return 0

        stat_div = stats_element.find("div", class_=icon_class)
        if stat_div:
            text = stat_div.get_text(strip=True)
            # Parse numbers like "1.2K", "5M"
            return self._parse_number(text)
        return 0

    def _parse_number(self, text: str) -> int:
        """Parse numbers with K/M suffixes."""
        text = text.replace(",", "").strip()

        if "K" in text.upper():
            return int(float(text.upper().replace("K", "")) * 1000)
        elif "M" in text.upper():
            return int(float(text.upper().replace("M", "")) * 1000000)

        try:
            return int(text)
        except ValueError:
            return 0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse tweet date string."""
        formats = [
            "%b %d, %Y · %I:%M %p UTC",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Twitter profile via Nitter."""
        url = self._get_nitter_url(f"/{username}")

        try:
            response = self._make_request(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract profile info
            profile = soup.find("div", class_="profile-card")
            if not profile:
                return None

            # Bio
            bio_elem = profile.find("div", class_="profile-bio")
            bio = bio_elem.get_text(strip=True) if bio_elem else ""

            # Stats
            stats = profile.find_all("div", class_="profile-stat-num")
            tweets_count = self._parse_number(stats[0].text) if len(stats) > 0 else 0
            following = self._parse_number(stats[1].text) if len(stats) > 1 else 0
            followers = self._parse_number(stats[2].text) if len(stats) > 2 else 0

            # Verified
            is_verified = bool(profile.find("span", class_="verified-icon"))

            return {
                "id": None,
                "username": username,
                "display_name": profile.find("a", class_="profile-card-fullname").text.strip() if profile.find("a", class_="profile-card-fullname") else username,
                "bio": bio,
                "followers_count": followers,
                "following_count": following,
                "posts_count": tweets_count,
                "is_verified": is_verified,
                "raw_data": {"html": str(profile)},
            }

        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get tweets for a user via Nitter."""
        url = self._get_nitter_url(f"/{username}")

        try:
            response = self._make_request(url)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            tweets = soup.find_all("div", class_="timeline-item")

            count = 0
            for tweet in tweets:
                if count >= limit:
                    break

                record = self._parse_tweet(tweet)
                if record:
                    yield record
                    count += 1

        except Exception as e:
            logger.error(f"Posts fetch failed: {e}")


# Also add requests import at top
import requests
