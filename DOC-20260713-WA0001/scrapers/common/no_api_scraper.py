"""No-API scraper using requests + BeautifulSoup + Selenium fallback.

This module provides scrapers that work WITHOUT official API keys,
using web scraping techniques instead.

IMPORTANT: These scrapers are for EDUCATIONAL purposes. 
Always respect robots.txt and platform Terms of Service.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional, List
import time
import random
import re
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from app.core.logging import logger
from app.services.proxy_service import proxy_rotator


class NoAPIScraper(ABC):
    """Base class for no-API web scrapers."""

    PLATFORM_NAME = "base"
    BASE_URL = ""

    def __init__(self, use_selenium: bool = False, headless: bool = True):
        self.session = requests.Session()
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None

        # Realistic browser headers
        self._setup_headers()

        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 2  # seconds between requests
        self.max_delay = 8

    def _setup_headers(self):
        """Setup realistic browser headers."""
        self.session.headers.update({
            "User-Agent": self._get_realistic_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        })

    def _get_realistic_user_agent(self) -> str:
        """Get a realistic user agent."""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(agents)

    def _random_delay(self):
        """Add random delay to mimic human behavior."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with anti-detection measures."""
        self._random_delay()

        # Rotate user agent occasionally
        if random.random() < 0.2:
            self.session.headers["User-Agent"] = self._get_realistic_user_agent()

        proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    proxies=proxy,
                    timeout=30,
                    allow_redirects=True,
                    **kwargs
                )

                if response.status_code == 200:
                    return response

                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = 60 * (attempt + 1)
                    logger.warning(f"Rate limited on {self.PLATFORM_NAME}, waiting {wait_time}s")
                    time.sleep(wait_time)

                elif response.status_code in [403, 401]:
                    # Blocked - try different proxy
                    if proxy:
                        proxy_rotator.mark_failed(proxy)
                        proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)
                    time.sleep(10)

                else:
                    logger.warning(f"Status {response.status_code} for {url}")
                    return None

            except requests.exceptions.ProxyError:
                if proxy:
                    proxy_rotator.mark_failed(proxy)
                    proxy = proxy_rotator.get_proxy(self.PLATFORM_NAME)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))

        return None

    def _init_selenium(self):
        """Initialize Selenium WebDriver for JavaScript-heavy pages."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument(f"--user-agent={self._get_realistic_user_agent()}")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        except Exception as e:
            logger.error(f"Failed to init Selenium: {e}")
            self.driver = None

    def _selenium_get(self, url: str) -> str:
        """Get page source using Selenium."""
        if not self.driver:
            self._init_selenium()

        if self.driver:
            self.driver.get(url)
            time.sleep(random.uniform(3, 7))  # Wait for JS to load
            return self.driver.page_source

        return ""

    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    @abstractmethod
    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search for content."""
        pass

    @abstractmethod
    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get profile info."""
        pass
