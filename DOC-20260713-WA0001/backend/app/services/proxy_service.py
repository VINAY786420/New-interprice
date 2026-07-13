"""Proxy rotation and management service."""
import random
import requests
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging import logger


class ProxyRotator:
    """Rotate proxies for scraping to avoid IP bans."""

    def __init__(self):
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.failed_proxies: set = set()
        self._load_proxies()

    def _load_proxies(self):
        """Load proxy list from configuration or API."""
        # Try to load from BrightData or similar provider
        if settings.PROXY_API_KEY:
            try:
                self._load_from_provider()
            except Exception as e:
                logger.warning("Failed to load proxies from provider", error=str(e))

        # Fallback to free proxies (for development)
        if not self.proxies:
            self._load_free_proxies()

    def _load_from_provider(self):
        """Load proxies from paid provider API."""
        # BrightData / Oxylabs integration
        # This is a placeholder - actual implementation depends on provider
        logger.info("Loading proxies from provider")

    def _load_free_proxies(self):
        """Load free proxies for development."""
        # Free proxy list (rotate frequently)
        free_proxies = [
            {"host": "proxy1.example.com", "port": 8080, "type": "http"},
            {"host": "proxy2.example.com", "port": 8080, "type": "http"},
        ]
        self.proxies = free_proxies
        logger.info(f"Loaded {len(self.proxies)} free proxies")

    def get_proxy(self, platform: str = None) -> Optional[Dict]:
        """Get next proxy in rotation."""
        if not self.proxies:
            return None

        # Filter out failed proxies
        available = [p for p in self.proxies if p.get("host") not in self.failed_proxies]

        if not available:
            # Reset failed proxies after cooldown
            self.failed_proxies.clear()
            available = self.proxies

        # Round-robin with randomization
        proxy = random.choice(available)

        return {
            "http": f"http://{proxy['host']}:{proxy['port']}",
            "https": f"http://{proxy['host']}:{proxy['port']}",
        }

    def mark_failed(self, proxy_dict: Dict):
        """Mark a proxy as failed."""
        if proxy_dict and "http" in proxy_dict:
            host = proxy_dict["http"].split(":")[1].strip("/")
            self.failed_proxies.add(host)
            logger.warning("Proxy marked as failed", host=host)

    def test_proxy(self, proxy_dict: Dict, timeout: int = 10) -> bool:
        """Test if a proxy is working."""
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies=proxy_dict,
                timeout=timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_proxy_count(self) -> int:
        """Get total number of available proxies."""
        return len(self.proxies)

    def get_healthy_proxy_count(self) -> int:
        """Get number of healthy proxies."""
        return len(self.proxies) - len(self.failed_proxies)


# Singleton instance
proxy_rotator = ProxyRotator()
