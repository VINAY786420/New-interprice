"""E-commerce scraper API routes for Amazon & Flipkart."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_active_user
from app.models.user import User
from app.core.logging import logger

router = APIRouter(prefix="/ecommerce", tags=["ecommerce"])

@router.get("/amazon/search")
def amazon_search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    sort: str = Query("relevance"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
):
    from scrapers import get_scraper
    scraper = get_scraper("amazon", prefer_api=False)
    try:
        results = list(scraper.search(keywords=[q], page=page, sort=sort, min_price=min_price, max_price=max_price))
        return {"platform": "amazon", "query": q, "page": page, "total_results": len(results), "products": results}
    except Exception as e:
        logger.error(f"Amazon search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/amazon/product/{asin}")
def amazon_product_details(asin: str, current_user: User = Depends(get_current_active_user)):
    from scrapers import get_scraper
    scraper = get_scraper("amazon", prefer_api=False)
    try:
        product = scraper.get_product_details(asin)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Amazon product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/amazon/bestsellers")
def amazon_bestsellers(
    category: str = Query("electronics"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    from scrapers import get_scraper
    scraper = get_scraper("amazon", prefer_api=False)
    try:
        results = list(scraper.get_bestsellers(category=category, limit=limit))
        return {"platform": "amazon", "category": category, "total": len(results), "products": results}
    except Exception as e:
        logger.error(f"Amazon bestsellers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/amazon/deals")
def amazon_deals(limit: int = Query(50, ge=1, le=100), current_user: User = Depends(get_current_active_user)):
    from scrapers import get_scraper
    scraper = get_scraper("amazon", prefer_api=False)
    try:
        results = list(scraper.get_deals(limit=limit))
        return {"platform": "amazon", "total": len(results), "deals": results}
    except Exception as e:
        logger.error(f"Amazon deals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/flipkart/search")
def flipkart_search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    sort: str = Query("relevance"),
    current_user: User = Depends(get_current_active_user),
):
    from scrapers import get_scraper
    scraper = get_scraper("flipkart", prefer_api=False)
    try:
        results = list(scraper.search(keywords=[q], page=page, sort=sort))
        return {"platform": "flipkart", "query": q, "page": page, "total_results": len(results), "products": results}
    except Exception as e:
        logger.error(f"Flipkart search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/flipkart/product/{product_id}")
def flipkart_product_details(product_id: str, current_user: User = Depends(get_current_active_user)):
    from scrapers import get_scraper
    scraper = get_scraper("flipkart", prefer_api=False)
    try:
        product = scraper.get_product_details(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flipkart product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/flipkart/deals")
def flipkart_deals(limit: int = Query(50, ge=1, le=100), current_user: User = Depends(get_current_active_user)):
    from scrapers import get_scraper
    scraper = get_scraper("flipkart", prefer_api=False)
    try:
        results = list(scraper.get_deals(limit=limit))
        return {"platform": "flipkart", "total": len(results), "deals": results}
    except Exception as e:
        logger.error(f"Flipkart deals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.close()

@router.get("/compare")
def compare_products(q: str = Query(...), limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_active_user)):
    from scrapers import get_scraper
    amazon_scraper = get_scraper("amazon", prefer_api=False)
    flipkart_scraper = get_scraper("flipkart", prefer_api=False)
    try:
        amazon_results = list(amazon_scraper.search(keywords=[q], limit=limit))
        flipkart_results = list(flipkart_scraper.search(keywords=[q], limit=limit))
        amazon_avg = sum(p["price"] or 0 for p in amazon_results) / len(amazon_results) if amazon_results else 0
        flipkart_avg = sum(p["price"] or 0 for p in flipkart_results) / len(flipkart_results) if flipkart_results else 0
        return {
            "query": q,
            "amazon": {"total": len(amazon_results), "products": amazon_results, "avg_price": round(amazon_avg, 2)},
            "flipkart": {"total": len(flipkart_results), "products": flipkart_results, "avg_price": round(flipkart_avg, 2)},
            "price_difference": round(amazon_avg - flipkart_avg, 2),
            "cheaper_platform": "amazon" if amazon_avg < flipkart_avg else "flipkart" if flipkart_avg < amazon_avg else "same",
        }
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        amazon_scraper.close()
        flipkart_scraper.close()
