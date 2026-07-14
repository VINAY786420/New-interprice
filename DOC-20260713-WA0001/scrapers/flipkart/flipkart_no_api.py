"""Flipkart scraper WITHOUT official API - using web scraping.

Scrapes:
- Product search results
- Product details (price, ratings, specs)
- Product reviews
- Deals of the day
- Category listings
"""
from typing import Iterator, Dict, Any, Optional, List
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger

class FlipkartNoAPIScraper(NoAPIScraper):
    PLATFORM_NAME = "flipkart"
    BASE_URL = "https://www.flipkart.com"
    SEARCH_URL = "https://www.flipkart.com/search"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_delay = 3
        self.max_delay = 8
        self.session.headers.update({
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        })

    def search(self, keywords: list, **filters) -> Iterator[Dict[str, Any]]:
        query = " ".join(keywords)
        params = {"q": query, "page": filters.get("page", 1)}
        if filters.get("sort"):
            sort_map = {"relevance": "relevance", "price_low": "price_asc", "price_high": "price_desc", "rating": "rating_desc", "newest": "recency_desc"}
            params["sort"] = sort_map.get(filters["sort"], "relevance")
        try:
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.select('div[data-id]')
            if not products:
                products = soup.select("._1AtVbE")
            for product in products:
                record = self._parse_search_result(product)
                if record:
                    yield record
        except Exception as e:
            logger.error(f"Flipkart search failed: {e}")

    def _parse_search_result(self, product) -> Optional[Dict[str, Any]]:
        try:
            product_id = product.get("data-id", "")
            if not product_id:
                return None
            title_elem = product.select_one("._4rR01T") or product.select_one(".s1Q9rs") or product.select_one("[class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else ""
            link_elem = product.select_one("a[class*='rp0']") or product.select_one("a[href*='/p/']")
            product_url = None
            if link_elem and link_elem.get("href"):
                product_url = urljoin(self.BASE_URL, link_elem["href"].split("?")[0])
            price = self._extract_price(product)
            original_price = self._extract_original_price(product)
            rating = self._extract_rating(product)
            review_count = self._extract_review_count(product)
            img_elem = product.select_one("img[class*='DByuf']") or product.select_one("img")
            image_url = img_elem.get("src") if img_elem else None
            badge_elem = product.select_one("._2Tpdn3") or product.select_one("[class*='badge']")
            badge = badge_elem.get_text(strip=True) if badge_elem else None
            fassured = bool(product.select_one("[class*='fassured']"))
            return {
                "platform": "flipkart",
                "source_id": product_id,
                "source_url": product_url,
                "title": title,
                "price": price,
                "original_price": original_price,
                "discount_percent": self._calc_discount(price, original_price),
                "currency": "INR",
                "rating": rating,
                "review_count": review_count,
                "image_url": image_url,
                "badge": badge,
                "is_fassured": fassured,
                "raw_data": {},
            }
        except Exception as e:
            logger.error(f"Flipkart parse error: {e}")
            return None

    def _extract_price(self, product) -> Optional[float]:
        try:
            for selector in ["._30jeq3", "._1_WHN1", "[class*='price']"]:
                elem = product.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    match = re.search(r"[₹]?\s*([\d,]+)", text)
                    if match:
                        return float(match.group(1).replace(",", ""))
            return None
        except Exception:
            return None

    def _extract_original_price(self, product) -> Optional[float]:
        try:
            elem = product.select_one("._3I9_wc") or product.select_one("._27UcVY")
            if elem:
                text = elem.get_text(strip=True)
                match = re.search(r"[₹]?\s*([\d,]+)", text)
                if match:
                    return float(match.group(1).replace(",", ""))
            return None
        except Exception:
            return None

    def _extract_rating(self, product) -> Optional[float]:
        try:
            elem = product.select_one("._3LWZlK") or product.select_one("[class*='rating']")
            if elem:
                text = elem.get_text(strip=True)
                match = re.search(r"([\d.]+)", text)
                if match:
                    rating = float(match.group(1))
                    if 0 <= rating <= 5:
                        return rating
            return None
        except Exception:
            return None

    def _extract_review_count(self, product) -> int:
        try:
            elem = product.select_one("._2_R_DZ") or product.select_one("[class*='review']")
            if elem:
                text = elem.get_text(strip=True)
                match = re.search(r"([\d,]+)", text)
                if match:
                    return int(match.group(1).replace(",", ""))
            return 0
        except Exception:
            return 0

    def _calc_discount(self, price, original) -> Optional[int]:
        if price and original and original > price:
            return int(((original - price) / original) * 100)
        return None

    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/p/{product_id}"
        try:
            response = self._make_request(url)
            if not response:
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.select_one(".B_NuCI") or soup.select_one("h1")
            title = title.get_text(strip=True) if title else ""
            price_elem = soup.select_one("._30jeq3")
            price = None
            if price_elem:
                match = re.search(r"[₹]?\s*([\d,]+)", price_elem.get_text(strip=True))
                if match:
                    price = float(match.group(1).replace(",", ""))
            desc_elem = soup.select_one("._2418kt")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            return {
                "platform": "flipkart",
                "source_id": product_id,
                "title": title,
                "price": price,
                "description": description,
                "url": url,
            }
        except Exception as e:
            logger.error(f"Flipkart product details failed: {e}")
            return None

    def get_deals(self, limit: int = 50) -> Iterator[Dict[str, Any]]:
        url = "https://www.flipkart.com/offers-store"
        try:
            response = self._make_request(url)
            if not response:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            deals = soup.select("[class*='deal']") or soup.select("._2B099V")
            for deal in deals[:limit]:
                title_elem = deal.select_one("[class*='title']") or deal.select_one("a")
                title = title_elem.get_text(strip=True) if title_elem else ""
                price_elem = deal.select_one("[class*='price']")
                price = None
                if price_elem:
                    match = re.search(r"[₹]?\s*([\d,]+)", price_elem.get_text(strip=True))
                    if match:
                        price = float(match.group(1).replace(",", ""))
                yield {
                    "platform": "flipkart",
                    "title": title,
                    "price": price,
                    "is_deal": True,
                }
        except Exception as e:
            logger.error(f"Flipkart deals failed: {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        return iter([])
