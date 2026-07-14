"""Pinterest scraper WITHOUT official API - using public search & pins.

Techniques:
1. Pinterest search results scraping
2. Public board/pin extraction
3. User profile scraping

Pinterest is relatively scraper-friendly for public content.
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


class PinterestNoAPIScraper(NoAPIScraper):
    """Pinterest scraper without official API keys."""

    PLATFORM_NAME = "pinterest"
    BASE_URL = "https://www.pinterest.com"
    SEARCH_URL = "https://www.pinterest.com/search/pins"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 3
        self.max_delay = 8
        self._csrftoken = None
        self._init_session()

    def _init_session(self):
        """Initialize Pinterest session and extract CSRF token."""
        try:
            response = self._make_request(self.BASE_URL)
            if response:
                # Extract CSRF token from cookies or page
                csrf_match = re.search(r'\"csrf_token\":\"([^\"]+)\"', response.text)
                if csrf_match:
                    self._csrftoken = csrf_match.group(1)

                # Also check cookies
                for cookie in response.cookies:
                    if cookie.name == "csrftoken":
                        self._csrftoken = cookie.value

                if self._csrftoken:
                    self.session.headers["X-CSRFToken"] = self._csrftoken

                logger.info("Pinterest session initialized", csrf=bool(self._csrftoken))

        except Exception as e:
            logger.error(f"Pinterest session init failed: {e}")

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Pinterest pins by keywords."""
        query = " ".join(keywords)

        # Pinterest uses a special search format
        search_term = quote(query)
        url = f"{self.BASE_URL}/search/pins/?q={search_term}"

        try:
            response = self._make_request(url)
            if not response:
                return

            # Pinterest loads data via JS, but initial HTML has some pins
            soup = BeautifulSoup(response.text, "html.parser")

            # Try to extract initial data from script tags
            scripts = soup.find_all("script")
            pins_data = []

            for script in scripts:
                if script.string and "initialReduxState" in script.string:
                    match = re.search(r'window\.initialReduxState\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            pins_data = self._extract_pins_from_redux(data)
                        except:
                            pass
                        break

            # Fallback: parse HTML pins
            if not pins_data:
                pin_elements = soup.find_all("div", {"data-test-id": "pin"})
                for elem in pin_elements:
                    pin = self._parse_pin_element(elem)
                    if pin:
                        yield pin
            else:
                for pin in pins_data:
                    yield pin

        except Exception as e:
            logger.error(f"Pinterest search failed: {e}")

    def _extract_pins_from_redux(self, data: dict) -> List[Dict[str, Any]]:
        """Extract pin data from Redux state."""
        pins = []

        try:
            # Navigate the Redux state to find pins
            resources = data.get("resources", {})
            data_cache = resources.get("data", {})

            for key, value in data_cache.items():
                if "Pin" in key and isinstance(value, dict):
                    pin_data = value.get("data", value)

                    pin = {
                        "platform": "pinterest",
                        "source_id": pin_data.get("id"),
                        "source_url": f"{self.BASE_URL}/pin/{pin_data.get('id')}/",
                        "username": pin_data.get("pinner", {}).get("username"),
                        "display_name": pin_data.get("pinner", {}).get("full_name"),
                        "post_content": pin_data.get("description", ""),
                        "posted_at": None,
                        "likes_count": pin_data.get("like_count", 0),
                        "comments_count": pin_data.get("comment_count", 0),
                        "repin_count": pin_data.get("repin_count", 0),
                        "image_url": pin_data.get("images", {}).get("orig", {}).get("url"),
                        "board_name": pin_data.get("board", {}).get("name"),
                        "raw_data": pin_data,
                    }
                    pins.append(pin)

        except Exception as e:
            logger.error(f"Redux extract error: {e}")

        return pins

    def _parse_pin_element(self, elem) -> Optional[Dict[str, Any]]:
        """Parse a pin HTML element."""
        try:
            # Extract image
            img = elem.find("img")
            image_url = img["src"] if img else None

            # Extract description
            desc_elem = elem.find("span", string=True)
            description = desc_elem.text.strip() if desc_elem else ""

            # Extract link
            link = elem.find("a", href=re.compile(r"/pin/"))
            pin_url = f"{self.BASE_URL}{link['href']}" if link else None
            pin_id = re.search(r"/pin/(\d+)/", link["href"]).group(1) if link else None

            # Extract pinner info
            pinner_elem = elem.find("a", href=re.compile(r"^/[^/]+/$"))
            username = pinner_elem["href"].strip("/") if pinner_elem else None

            return {
                "platform": "pinterest",
                "source_id": pin_id,
                "source_url": pin_url,
                "username": username,
                "display_name": username,
                "post_content": description,
                "posted_at": None,
                "likes_count": 0,
                "comments_count": 0,
                "repin_count": 0,
                "image_url": image_url,
                "board_name": None,
                "raw_data": {"html": str(elem)},
            }

        except Exception as e:
            logger.error(f"Pin parse error: {e}")
            return None

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get Pinterest user profile."""
        url = f"{self.BASE_URL}/{username}/"

        try:
            response = self._make_request(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract from Redux state
            scripts = soup.find_all("script")
            user_data = None

            for script in scripts:
                if script.string and "initialReduxState" in script.string:
                    match = re.search(r'window\.initialReduxState\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            resources = data.get("resources", {}).get("data", {})
                            for key, value in resources.items():
                                if "User" in key:
                                    user_data = value.get("data", value)
                                    break
                        except:
                            pass
                        break

            if not user_data:
                return None

            return {
                "platform": "pinterest",
                "username": username,
                "display_name": user_data.get("full_name", username),
                "bio": user_data.get("about", ""),
                "followers_count": user_data.get("follower_count", 0),
                "following_count": user_data.get("following_count", 0),
                "pins_count": user_data.get("pin_count", 0),
                "boards_count": user_data.get("board_count", 0),
                "profile_image": user_data.get("image_xlarge_url"),
                "website": user_data.get("domain_url"),
                "raw_data": user_data,
            }

        except Exception as e:
            logger.error(f"Pinterest profile fetch failed: {e}")
            return None

    def get_board_pins(self, username: str, board_name: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get pins from a specific board."""
        url = f"{self.BASE_URL}/{username}/{board_name}/"

        try:
            response = self._make_request(url)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            scripts = soup.find_all("script")

            for script in scripts:
                if script.string and "initialReduxState" in script.string:
                    match = re.search(r'window\.initialReduxState\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            pins = self._extract_pins_from_redux(data)
                            for pin in pins[:limit]:
                                yield pin
                        except:
                            pass
                        break

        except Exception as e:
            logger.error(f"Pinterest board fetch failed: {e}")

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get pins for a Pinterest user."""
        url = f"{self.BASE_URL}/{username}/pins/"

        try:
            response = self._make_request(url)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            scripts = soup.find_all("script")

            for script in scripts:
                if script.string and "initialReduxState" in script.string:
                    match = re.search(r'window\.initialReduxState\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            pins = self._extract_pins_from_redux(data)
                            for pin in pins[:limit]:
                                yield pin
                        except:
                            pass
                        break

        except Exception as e:
            logger.error(f"Pinterest posts fetch failed: {e}")
