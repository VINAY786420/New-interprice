"""Amazon India scraper WITHOUT official API - using web scraping."""
from typing import Iterator, Dict, Any, Optional, List
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapers.common.no_api_scraper import NoAPIScraper
from app.core.logging import logger

class AmazonNoAPIScraper(NoAPIScraper):
    PLATFORM_NAME = "amazon"
    BASE_URL = "https://www.amazon.in"
    SEARCH_URL = "https://www.amazon.in/s"

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
        params = {"k": query, "page": filters.get("page", 1)}
        if filters.get("category"):
            params["i"] = filters["category"]
        sort_map = {"relevance": "relevanceblender", "price_low": "price-asc-rank", "price_high": "price-desc-rank", "rating": "review-rank"}
        if filters.get("sort"):
            params["s"] = sort_map.get(filters["sort"], "relevanceblender")
        try:
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.select('div[data-component-type="s-search-result"]')
            if not products:
                products = soup.select("div.s-result-item")
            for product in products:
                record = self._parse_search_result(product)
                if record:
                    yield record
        except Exception as e:
            logger.error(f"Amazon search failed: {e}")

    def _parse_search_result(self, product) -> Optional[Dict[str, Any]]:
        try:
            asin = product.get("data-asin", "")
            if not asin:
                asin_elem = product.select_one("[data-asin]")
                if asin_elem:
                    asin = asin_elem.get("data-asin", "")
            if not asin:
                return None
            title_elem = product.select_one("h2 a span") or product.select_one(".a-text-normal")
            title = title_elem.get_text(strip=True) if title_elem else ""
            link_elem = product.select_one("h2 a")
            product_url = None
            if link_elem and link_elem.get("href"):
                product_url = urljoin(self.BASE_URL, link_elem["href"].split("?")[0])
            price = self._extract_price(product)
            original_price = self._extract_original_price(product)
            rating = self._extract_rating(product)
            review_count = self._extract_review_count(product)
            img_elem = product.select_one("img")
            image_url = img_elem.get("src") if img_elem else None
            badge_elem = product.select_one(".a-badge-text")
            badge = badge_elem.get_text(strip=True) if badge_elem else None
            is_prime = bool(product.select_one(".a-icon-prime"))
            is_sponsored = "Sponsored" in str(product)
            return {
                "platform": "amazon",
                "source_id": asin,
                "source_url": product_url or f"{self.BASE_URL}/dp/{asin}",
                "title": title,
                "price": price,
                "original_price": original_price,
                "discount_percent": self._calc_discount(price, original_price),
                "currency": "INR",
                "rating": rating,
                "review_count": review_count,
                "image_url": image_url,
                "badge": badge,
                "is_prime": is_prime,
                "is_sponsored": is_sponsored,
                "raw_data": {},
            }
        except Exception as e:
            logger.error(f"Amazon parse error: {e}")
            return None

    def _extract_price(self, product) -> Optional[float]:
        try:
            for selector in [".a-price .a-offscreen", ".a-price-whole"]:
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
            elem = product.select_one(".a-text-price .a-offscreen")
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
            elem = product.select_one(".a-icon-alt")
            if elem:
                text = elem.get("aria-label", "") or elem.get_text(strip=True)
                match = re.search(r"([\d.]+)\s*out of", text)
                if match:
                    return float(match.group(1))
            return None
        except Exception:
            return None

    def _extract_review_count(self, product) -> int:
        try:
            elem = product.select_one("[href*='reviews'] span")
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

    def get_product_details(self, asin: str) -> Optional[Dict[str, Any]]:
        url = self.PRODUCT_URL.format(asin)
        try:
            response = self._make_request(url)
            if not response:
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.select_one("#productTitle")
            title = title.get_text(strip=True) if title else ""
            price_elem = soup.select_one(".a-price .a-offscreen")
            price = None
            if price_elem:
                match = re.search(r"[₹]?\s*([\d,]+)", price_elem.get_text(strip=True))
                if match:
                    price = float(match.group(1).replace(",", ""))
            desc_elem = soup.select_one("#feature-bullets")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            brand_elem = soup.select_one("[class*='brand']")
            brand = brand_elem.get_text(strip=True) if brand_elem else ""
            return {
                "platform": "amazon",
                "source_id": asin,
                "title": title,
                "price": price,
                "brand": brand,
                "description": description,
                "url": url,
            }
        except Exception as e:
            logger.error(f"Amazon product details failed: {e}")
            return None

    def get_bestsellers(self, category: str = "electronics", limit: int = 50) -> Iterator[Dict[str, Any]]:
        url = self.BESTSELLERS_URL.format(category)
        try:
            response = self._make_request(url)
            if not response:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select(".zg-grid-general-faceout")
            for i, item in enumerate(items[:limit]):
                title_elem = item.select_one("[class*='title']") or item.select_one("a span")
                title = title_elem.get_text(strip=True) if title_elem else ""
                link_elem = item.select_one("a")
                product_url = urljoin(self.BASE_URL, link_elem["href"]) if link_elem else None
                price_elem = item.select_one(".a-price .a-offscreen")
                price = None
                if price_elem:
                    match = re.search(r"[₹]?\s*([\d,]+)", price_elem.get_text(strip=True))
                    if match:
                        price = float(match.group(1).replace(",", ""))
                yield {
                    "platform": "amazon",
                    "rank": i + 1,
                    "title": title,
                    "price": price,
                    "url": product_url,
                    "category": category,
                    "is_bestseller": True,
                }
        except Exception as e:
            logger.error(f"Amazon bestsellers failed: {e}")

    def get_deals(self, limit: int = 50) -> Iterator[Dict[str, Any]]:
        try:
            response = self._make_request(self.DEALS_URL)
            if not response:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            deals = soup.select("[data-action='gbdeal-dealaction']")
            for deal in deals[:limit]:
                title_elem = deal.select_one("[class*='title']")
                title = title_elem.get_text(strip=True) if title_elem else ""
                price_elem = deal.select_one(".a-price .a-offscreen")
                price = None
                if price_elem:
                    match = re.search(r"[₹]?\s*([\d,]+)", price_elem.get_text(strip=True))
                    if match:
                        price = float(match.group(1).replace(",", ""))
                discount_elem = deal.select_one("[class*='discount']")
                discount = discount_elem.get_text(strip=True) if discount_elem else None
                yield {
                    "platform": "amazon",
                    "title": title,
                    "price": price,
                    "discount_text": discount,
                    "is_deal": True,
                }
        except Exception as e:
            logger.error(f"Amazon deals failed: {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        return None

    def get_posts(self, username: str, limit: int = 50) -> Iterator[Dict[str, Any]]:
        return iter([])
