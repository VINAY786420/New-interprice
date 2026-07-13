"""Celery background tasks."""
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import random

from app.models.base import SessionLocal
from app.models.collection import Collection, CollectionStatus
from app.models.data_record import DataRecord
from app.models.scraper_node import ScraperNode, NodeStatus
from app.models.proxy import Proxy, ProxyStatus
from app.services.sentiment_service import sentiment_analyzer
from app.services.proxy_service import proxy_rotator
from app.core.logging import logger
from scrapers import get_scraper


@shared_task(bind=True, max_retries=3)
def start_collection_job(self, collection_id: int):
    """Start a data collection job using appropriate scraper."""
    db = SessionLocal()

    try:
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            logger.error("Collection not found", collection_id=collection_id)
            return

        # Update status
        collection.status = CollectionStatus.RUNNING
        db.commit()

        logger.info(
            "Starting collection job",
            collection_id=collection_id,
            platforms=collection.platforms,
            keywords=collection.keywords
        )

        # Get scrapers for each platform
        scrapers = {}
        for platform in collection.platforms:
            try:
                scrapers[platform] = get_scraper(platform, prefer_api=False)  # Use no-API by default
                logger.info(f"Initialized scraper for {platform}")
            except Exception as e:
                logger.error(f"Failed to initialize scraper for {platform}", error=str(e))

        if not scrapers:
            logger.error("No scrapers available")
            collection.status = CollectionStatus.FAILED
            collection.error_message = "No scrapers could be initialized"
            db.commit()
            return

        # Collect data
        total_collected = 0
        target = collection.volume_target

        for platform, scraper in scrapers.items():
            if total_collected >= target:
                break

            try:
                logger.info(f"Scraping {platform}...")

                # Search for content
                for record_data in scraper.search(
                    keywords=collection.keywords,
                    limit=min(target - total_collected, 1000)
                ):
                    if total_collected >= target:
                        break

                    if collection.status == CollectionStatus.CANCELLED:
                        break

                    # Enrich data
                    record_data = enrich_record(record_data, collection.data_fields)

                    # Create database record
                    record = create_data_record(record_data, collection.id)
                    db.add(record)
                    total_collected += 1

                    # Commit batch
                    if total_collected % 100 == 0:
                        collection.volume_collected = total_collected
                        collection.progress_percent = int((total_collected / target) * 100)
                        db.commit()
                        logger.info(f"Collected {total_collected}/{target} records")

                scraper.close()

            except Exception as e:
                logger.error(f"Scraper error for {platform}", error=str(e))
                continue

        # Final update
        collection.volume_collected = total_collected
        collection.progress_percent = 100 if total_collected >= target else int((total_collected / target) * 100)

        if collection.status != CollectionStatus.CANCELLED:
            collection.status = CollectionStatus.COMPLETED if total_collected >= target else CollectionStatus.COMPLETED
            collection.last_run_at = datetime.utcnow()

        db.commit()

        logger.info(
            "Collection job completed",
            collection_id=collection_id,
            records_collected=total_collected
        )

    except Exception as exc:
        logger.error("Collection job failed", collection_id=collection_id, error=str(exc))
        if collection:
            collection.status = CollectionStatus.FAILED
            collection.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()


def enrich_record(record_data: dict, data_fields: list) -> dict:
    """Enrich record with additional data."""
    # Sentiment analysis
    if "sentiment" in data_fields and record_data.get("post_content"):
        sentiment = sentiment_analyzer.analyze(record_data["post_content"])
        record_data["sentiment_score"] = sentiment["score"]
        record_data["sentiment_label"] = sentiment["label"]

    # Extract hashtags
    if "hashtags" in data_fields and record_data.get("post_content"):
        import re
        record_data["hashtags"] = re.findall(r'#(\w+)', record_data["post_content"])

    # Extract mentions
    if "mentions" in data_fields and record_data.get("post_content"):
        import re
        record_data["mentions"] = re.findall(r'@(\w+)', record_data["post_content"])

    return record_data


def create_data_record(record_data: dict, collection_id: int) -> DataRecord:
    """Create a DataRecord from scraped data."""
    return DataRecord(
        platform=record_data.get("platform", "unknown"),
        source_id=record_data.get("source_id"),
        source_url=record_data.get("source_url"),
        username=record_data.get("username"),
        display_name=record_data.get("display_name"),
        bio=record_data.get("bio"),
        followers_count=record_data.get("followers_count", 0),
        following_count=record_data.get("following_count", 0),
        posts_count=record_data.get("posts_count", 0),
        engagement_rate=record_data.get("engagement_rate"),
        post_content=record_data.get("post_content"),
        post_type=record_data.get("post_type"),
        hashtags=record_data.get("hashtags", []),
        mentions=record_data.get("mentions", []),
        media_urls=record_data.get("media_urls", []),
        thumbnail_url=record_data.get("thumbnail_url"),
        likes_count=record_data.get("likes_count", 0),
        comments_count=record_data.get("comments_count", 0),
        shares_count=record_data.get("shares_count", 0),
        views_count=record_data.get("views_count", 0),
        sentiment_score=record_data.get("sentiment_score"),
        sentiment_label=record_data.get("sentiment_label"),
        language=record_data.get("language"),
        topics=record_data.get("topics", []),
        country=record_data.get("country"),
        city=record_data.get("city"),
        coordinates=record_data.get("coordinates"),
        estimated_age_range=record_data.get("estimated_age_range"),
        estimated_gender=record_data.get("estimated_gender"),
        interests=record_data.get("interests", []),
        posted_at=record_data.get("posted_at"),
        collected_at=datetime.utcnow(),
        is_verified=record_data.get("is_verified", False),
        is_business_account=record_data.get("is_business_account", False),
        pii_redacted=True,
        consent_status="public",
        raw_data=record_data.get("raw_data"),
        collection_id=collection_id,
    )


@shared_task
def cleanup_old_records():
    """Clean up old records to manage storage."""
    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        count = db.query(DataRecord).filter(DataRecord.created_at < cutoff_date).delete()
        db.commit()
        logger.info("Cleaned up old records", deleted_count=count, cutoff=cutoff_date)
    finally:
        db.close()


@shared_task
def update_proxy_health():
    """Update proxy health status."""
    db = SessionLocal()

    try:
        proxies = db.query(Proxy).filter(Proxy.status != ProxyStatus.DEAD).all()

        for proxy in proxies:
            proxy_dict = {
                "http": f"http://{proxy.host}:{proxy.port}",
                "https": f"http://{proxy.host}:{proxy.port}",
            }

            is_healthy = proxy_rotator.test_proxy(proxy_dict, timeout=10)

            if not is_healthy:
                proxy.failed_requests += 1
                if proxy.failed_requests > 10:
                    proxy.status = ProxyStatus.BANNED
            else:
                proxy.success_rate = (proxy.success_rate * 0.9) + (10 * 0.1)
                proxy.failed_requests = max(0, proxy.failed_requests - 1)

        db.commit()
        logger.info("Updated proxy health", proxy_count=len(proxies))
    finally:
        db.close()


@shared_task
def generate_daily_reports():
    """Generate daily analytics reports."""
    db = SessionLocal()

    try:
        today = datetime.utcnow().date()
        daily_records = db.query(DataRecord).filter(
            DataRecord.collected_at >= datetime.combine(today, datetime.min.time())
        ).count()

        logger.info("Generated daily report", date=today, records=daily_records)
    finally:
        db.close()
