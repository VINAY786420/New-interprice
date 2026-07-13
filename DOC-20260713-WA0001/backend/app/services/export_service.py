"""Data export service for various formats."""
import csv
import json
import io
from typing import List
from datetime import datetime

from app.models.data_record import DataRecord
from app.core.config import settings


def export_data(records: List[DataRecord], format: str, include_raw: bool = False) -> dict:
    """Export data records to specified format."""

    if format == "csv":
        return export_to_csv(records, include_raw)
    elif format == "json":
        return export_to_json(records, include_raw)
    elif format == "excel":
        return export_to_excel(records, include_raw)
    elif format == "sql":
        return export_to_sql(records, include_raw)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_to_csv(records: List[DataRecord], include_raw: bool) -> dict:
    """Export records to CSV format."""
    output = io.StringIO()

    # Define headers
    headers = [
        "id", "platform", "username", "display_name", "followers_count",
        "following_count", "posts_count", "engagement_rate", "post_content",
        "hashtags", "likes_count", "comments_count", "shares_count",
        "sentiment_score", "sentiment_label", "country", "city",
        "interests", "posted_at", "is_verified", "is_business_account"
    ]

    if include_raw:
        headers.append("raw_data")

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    for record in records:
        row = {
            "id": record.id,
            "platform": record.platform,
            "username": record.username,
            "display_name": record.display_name,
            "followers_count": record.followers_count,
            "following_count": record.following_count,
            "posts_count": record.posts_count,
            "engagement_rate": record.engagement_rate,
            "post_content": record.post_content,
            "hashtags": json.dumps(record.hashtags) if record.hashtags else "",
            "likes_count": record.likes_count,
            "comments_count": record.comments_count,
            "shares_count": record.shares_count,
            "sentiment_score": record.sentiment_score,
            "sentiment_label": record.sentiment_label,
            "country": record.country,
            "city": record.city,
            "interests": json.dumps(record.interests) if record.interests else "",
            "posted_at": record.posted_at.isoformat() if record.posted_at else "",
            "is_verified": record.is_verified,
            "is_business_account": record.is_business_account,
        }

        if include_raw:
            row["raw_data"] = json.dumps(record.raw_data) if record.raw_data else ""

        writer.writerow(row)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{timestamp}.csv"

    return {
        "format": "csv",
        "file_url": f"/exports/{filename}",
        "file_size": len(output.getvalue()),
        "record_count": len(records),
        "content": output.getvalue()
    }


def export_to_json(records: List[DataRecord], include_raw: bool) -> dict:
    """Export records to JSON format."""
    data = []

    for record in records:
        item = {
            "id": record.id,
            "platform": record.platform,
            "username": record.username,
            "display_name": record.display_name,
            "profile": {
                "followers": record.followers_count,
                "following": record.following_count,
                "posts": record.posts_count,
                "engagement_rate": record.engagement_rate,
                "is_verified": record.is_verified,
                "is_business_account": record.is_business_account,
            },
            "content": {
                "text": record.post_content,
                "hashtags": record.hashtags,
                "media_urls": record.media_urls,
            },
            "engagement": {
                "likes": record.likes_count,
                "comments": record.comments_count,
                "shares": record.shares_count,
                "views": record.views_count,
            },
            "enrichment": {
                "sentiment": {
                    "score": record.sentiment_score,
                    "label": record.sentiment_label,
                },
                "language": record.language,
                "topics": record.topics,
            },
            "location": {
                "country": record.country,
                "city": record.city,
                "coordinates": record.coordinates,
            },
            "demographics": {
                "estimated_age": record.estimated_age_range,
                "estimated_gender": record.estimated_gender,
                "interests": record.interests,
            },
            "metadata": {
                "posted_at": record.posted_at.isoformat() if record.posted_at else None,
                "collected_at": record.collected_at.isoformat() if record.collected_at else None,
                "source_id": record.source_id,
                "source_url": record.source_url,
            }
        }

        if include_raw:
            item["raw_data"] = record.raw_data

        data.append(item)

    output = json.dumps(data, indent=2, ensure_ascii=False)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{timestamp}.json"

    return {
        "format": "json",
        "file_url": f"/exports/{filename}",
        "file_size": len(output),
        "record_count": len(records),
        "content": output
    }


def export_to_excel(records: List[DataRecord], include_raw: bool) -> dict:
    """Export records to Excel format."""
    try:
        import pandas as pd

        data = []
        for record in records:
            data.append({
                "ID": record.id,
                "Platform": record.platform,
                "Username": record.username,
                "Display Name": record.display_name,
                "Followers": record.followers_count,
                "Following": record.following_count,
                "Posts": record.posts_count,
                "Engagement Rate": record.engagement_rate,
                "Content": record.post_content,
                "Hashtags": ", ".join(record.hashtags) if record.hashtags else "",
                "Likes": record.likes_count,
                "Comments": record.comments_count,
                "Shares": record.shares_count,
                "Sentiment": record.sentiment_label,
                "Country": record.country,
                "City": record.city,
                "Posted At": record.posted_at,
                "Verified": record.is_verified,
                "Business": record.is_business_account,
            })

        df = pd.DataFrame(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Data", index=False)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.xlsx"

        return {
            "format": "excel",
            "file_url": f"/exports/{filename}",
            "file_size": len(output.getvalue()),
            "record_count": len(records),
            "content": output.getvalue()
        }
    except ImportError:
        raise ImportError("pandas and openpyxl required for Excel export")


def export_to_sql(records: List[DataRecord], include_raw: bool) -> dict:
    """Export records as SQL INSERT statements."""
    statements = []

    for record in records:
        stmt = f"""
INSERT INTO data_records (
    platform, username, display_name, followers_count, following_count,
    posts_count, engagement_rate, post_content, hashtags, likes_count,
    comments_count, shares_count, sentiment_score, sentiment_label,
    country, city, posted_at, is_verified, is_business_account
) VALUES (
    '{record.platform}', '{record.username}', '{record.display_name or ""}',
    {record.followers_count}, {record.following_count}, {record.posts_count},
    {record.engagement_rate or 0}, '{record.post_content or ""}',
    '{json.dumps(record.hashtags) if record.hashtags else "[]"}',
    {record.likes_count}, {record.comments_count}, {record.shares_count},
    {record.sentiment_score or 0}, '{record.sentiment_label or ""}',
    '{record.country or ""}', '{record.city or ""}',
    '{record.posted_at.isoformat() if record.posted_at else ""}',
    {record.is_verified}, {record.is_business_account}
);
"""
        statements.append(stmt)

    output = "\n".join(statements)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{timestamp}.sql"

    return {
        "format": "sql",
        "file_url": f"/exports/{filename}",
        "file_size": len(output),
        "record_count": len(records),
        "content": output
    }
