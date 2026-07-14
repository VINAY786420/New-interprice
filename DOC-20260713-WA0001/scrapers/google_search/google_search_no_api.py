"""Google Search scraper WITHOUT official API - using organic search results.

Techniques:
1. Standard Google search results scraping
2. News search
3. Image search metadata
4. Site-specific search

Uses rotating user agents and delays to avoid blocks.
"""
from typing import Iterator, Dict, Any, Optional, List
import re
import json
import time
import random
from datetime import datetime
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup

from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger


class GoogleSearchNoAPIScraper(NoAPIScraper):
    """Google Search scraper without official API keys."""

    PLATFORM_NAME = "google_search"
    BASE_URL = "https://www.google.com"
    SEARCH_URL = "https://www.google.com/search"
    NEWS_URL = "https://www.google.com/search"
    IMAGES_URL = "https://www.google.com/search"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 4
        self.max_delay = 10
        # Google requires very realistic headers
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
        })

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search Google organic results by keywords."""
        query = " ".join(keywords)

        search_type = filters.get("type", "web")  # web, news, images

        if search_type == "news":
            yield from self._search_news(query, **filters)
        elif search_type == "images":
            yield from self._search_images(query, **filters)
        else:
            yield from self._search_web(query, **filters)

    def _search_web(self, query: str, **filters) -> Iterator[Dict[str, Any]]:
        """Search web results."""
        params = {
            "q": query,
            "num": min(filters.get("limit", 10), 100),
            "start": filters.get("offset", 0),
            "hl": filters.get("lang", "en"),
        }

        # Site-specific search
        if filters.get("site"):
            params["q"] = f"site:{filters['site']} {query}"

        # Time filter
        if filters.get("time"):
            time_map = {
                "day": "d",
                "week": "w", 
                "month": "m",
                "year": "y",
            }
            params["tbs"] = f"qdr:{time_map.get(filters['time'], 'm')}"

        try:
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract search results
            results = soup.find_all("div", class_=re.compile(r"g|yuRUbf"))

            for result in results:
                record = self._parse_web_result(result, query)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Google web search failed: {e}")

    def _parse_web_result(self, result, query: str) -> Optional[Dict[str, Any]]:
        """Parse a Google web search result."""
        try:
            # Extract title
            title_elem = result.find("h3")
            title = title_elem.text.strip() if title_elem else ""

            # Extract URL
            link_elem = result.find("a", href=True)
            url = None
            if link_elem:
                href = link_elem["href"]
                if href.startswith("/url?q="):
                    url = unquote(re.search(r"/url\?q=([^&]+)", href).group(1)) if re.search(r"/url\?q=([^&]+)", href) else None
                elif href.startswith("http"):
                    url = href

            # Extract snippet/description
            snippet_elem = result.find("div", class_=re.compile(r"VwiC3b|s3v94d|lyLwlc"))
            if not snippet_elem:
                snippet_elem = result.find("span", class_=re.compile(r"aCOpRe|st"))
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            # Extract domain
            domain = None
            if url:
                domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
                domain = domain_match.group(1) if domain_match else None

            # Extract date if present
            date_elem = result.find("span", class_=re.compile(r"MUxGbd|fG8Fp"))
            date_text = date_elem.text.strip() if date_elem else None

            return {
                "platform": "google_search",
                "source_id": None,
                "source_url": url,
                "username": domain,
                "display_name": domain,
                "post_content": title + "\n" + snippet,
                "posted_at": None,
                "title": title,
                "snippet": snippet,
                "domain": domain,
                "search_query": query,
                "date_text": date_text,
                "likes_count": 0,
                "comments_count": 0,
                "raw_data": {"html": str(result)},
            }

        except Exception as e:
            logger.error(f"Google result parse error: {e}")
            return None

    def _search_news(self, query: str, **filters) -> Iterator[Dict[str, Any]]:
        """Search Google News results."""
        params = {
            "q": query,
            "tbm": "nws",
            "num": min(filters.get("limit", 10), 100),
            "hl": filters.get("lang", "en"),
        }

        if filters.get("time"):
            time_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
            params["tbs"] = f"qdr:{time_map.get(filters['time'], 'm')}"

        try:
            response = self._make_request(self.NEWS_URL, params=params)
            if not response:
                return

            soup = BeautifulSoup(response.text, "html.parser")

            # News results have different structure
            news_results = soup.find_all("div", class_=re.compile(r"g|SoaBEf|WlydOe"))

            for result in news_results:
                record = self._parse_news_result(result, query)
                if record:
                    yield record

        except Exception as e:
            logger.error(f"Google news search failed: {e}")

    def _parse_news_result(self, result, query: str) -> Optional[Dict[str, Any]]:
        """Parse a Google News result."""
        try:
            # Extract title
            title_elem = result.find("div", role="heading") or result.find("h3") or result.find("a", class_=re.compile(r"nDgy9d"))
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract URL
            link_elem = result.find("a", href=True)
            url = None
            if link_elem:
                href = link_elem["href"]
                if href.startswith("/url?q="):
                    match = re.search(r"/url\?q=([^&]+)", href)
                    url = unquote(match.group(1)) if match else None
                elif href.startswith("http"):
                    url = href

            # Extract source and time
            source_elem = result.find("div", class_=re.compile(r"UPmit|MgUUmf"))
            source = source_elem.get_text(strip=True) if source_elem else ""

            # Extract snippet
            snippet_elem = result.find("div", class_=re.compile(r"VwiC3b|GI74Re"))
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            # Extract thumbnail
            img = result.find("img")
            thumbnail = img["src"] if img and img.get("src") else None

            return {
                "platform": "google_search",
                "source_id": None,
                "source_url": url,
                "username": source,
                "display_name": source,
                "post_content": title + "\n" + snippet,
                "posted_at": None,
                "title": title,
                "snippet": snippet,
                "source": source,
                "search_query": query,
                "news_type": True,
                "thumbnail": thumbnail,
                "likes_count": 0,
                "comments_count": 0,
                "raw_data": {"html": str(result)},
            }

        except Exception as e:
            logger.error(f"Google news parse error: {e}")
            return None

    def _search_images(self, query: str, **filters) -> Iterator[Dict[str, Any]]:
        """Search Google Images metadata."""
        params = {
            "q": query,
            "tbm": "isch",
            "hl": filters.get("lang", "en"),
        }

        try:
            response = self._make_request(self.IMAGES_URL, params=params)
            if not response:
                return

            # Google Images loads via JS, but we can extract from initial data
            soup = BeautifulSoup(response.text, "html.parser")

            # Try to find image data in script tags
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "AF_initDataCallback" in script.string:
                    # Extract image data from Google's internal format
                    matches = re.findall(r'"([^"]+\.(?:jpg|jpeg|png|gif|webp))[^"]*"', script.string)
                    for i, img_url in enumerate(matches[:filters.get("limit", 20)]):
                        yield {
                            "platform": "google_search",
                            "source_id": f"img_{i}",
                            "source_url": img_url,
                            "username": None,
                            "display_name": None,
                            "post_content": query,
                            "posted_at": None,
                            "image_url": img_url,
                            "search_query": query,
                            "image_type": True,
                            "likes_count": 0,
                            "comments_count": 0,
                            "raw_data": {},
                        }

        except Exception as e:
            logger.error(f"Google images search failed: {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Google Search doesn't have user profiles - search for entity instead."""
        # Search for knowledge panel info
        results = list(self.search([username], type="web", limit=5))

        if results:
            return {
                "platform": "google_search",
                "username": username,
                "display_name": username,
                "bio": results[0].get("snippet", ""),
                "website": results[0].get("source_url"),
                "raw_data": {"top_results": results[:5]},
            }
        return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Get search results for a specific entity."""
        yield from self.search([username], limit=limit)

    def search_site(self, site: str, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        """Search within a specific site."""
        filters["site"] = site
        yield from self.search(keywords, **filters)

    def get_related_keywords(self, keyword: str) -> List[str]:
        """Get related keywords from Google 'People also ask' and related searches."""
        related = []

        try:
            params = {"q": keyword}
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return related

            soup = BeautifulSoup(response.text, "html.parser")

            # People also ask
            paa = soup.find_all("div", class_=re.compile(r"related-question-pair|g-blk"))
            for item in paa:
                text = item.get_text(strip=True)
                if text and "?" in text:
                    related.append(text)

            # Related searches
            related_searches = soup.find_all("a", class_=re.compile(r"nPDzT|k8XOCe"))
            for item in related_searches:
                text = item.get_text(strip=True)
                if text and text not in related:
                    related.append(text)

            return related[:20]

        except Exception as e:
            logger.error(f"Related keywords fetch failed: {e}")
            return related
