"""Base scraper class with common functionality."""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional
import time
import random
import requests
from datetime import datetime

from app.core.logging import logger
from app.services.proxy_service import proxy_rotator


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""

    PLATFORM_NAME = "base"
    BASE_URL = ""

    def __init__(self, proxy_enabled: bool = True, rate_limit: int = 60):
        self.proxy_enabled = proxy_enabled
        self.rate_limit = rate_limit  # requests per minute
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_count = 0

        # Set default headers
        self.session.headers.update({
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        min_interval = 60.0 / self.rate_limit
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed + random.uniform(0.5, 2.0)
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with proxy and retry logic."""
        self._rate_limit()

        proxy = None
        if self.proxy_enabled:
            proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    proxies=proxy,
                    timeout=30,
                    **kwargs
                )

                if response.status_code == 200:
                    return response

                elif response.status_code in [403, 429, 503]:
                    # Blocked or rate limited
                    if proxy:
                        proxy_rotator.mark_failed(proxy)
                        proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)
                    time.sleep(2 ** attempt)  # Exponential backoff

                else:
                    logger.warning(
                        f"Unexpected status code",
                        status_code=response.status_code,
                        url=url,
                        platform=self.PLATFORM_NAME
                    )
                    return None

            except requests.exceptions.ProxyError:
                if proxy:
                    proxy_rotator.mark_failed(proxy)
                    proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)
            except Exception as e:
                logger.error(f"Request failed", error=str(e), url=url)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    @abstractmethod
    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search for content based on keywords."""
        pass

    @abstractmethod
    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get profile information for a user."""
        pass

    @abstractmethod
    def get_posts(self, username: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Get posts for a user."""
        pass

    def normalize_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw data to standard format."""
        return {
            "platform": self.PLATFORM_NAME,
            "source_id": raw_data.get("id"),
            "source_url": raw_data.get("url"),
            "username": raw_data.get("username"),
            "display_name": raw_data.get("display_name"),
            "post_content": raw_data.get("content", ""),
            "posted_at": raw_data.get("created_at"),
            "raw_data": raw_data,
        }
