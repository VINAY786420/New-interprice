"""Data records API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
import json

from app.models.base import get_db
from app.models.data_record import DataRecord
from app.models.user import User
from app.schemas.data_record import DataRecordResponse, DataRecordFilter, DataExportRequest
from app.api.auth import get_current_active_user
from app.services.export_service import export_data
from app.core.logging import logger

router = APIRouter()


@router.get("/", response_model=List[DataRecordResponse])
def list_records(
    platform: Optional[str] = None,
    country: Optional[str] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    sentiment: Optional[str] = None,
    keyword: Optional[str] = None,
    is_verified: Optional[bool] = None,
    is_business: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List data records with filters."""
    query = db.query(DataRecord)

    if platform:
        query = query.filter(DataRecord.platform == platform)
    if country:
        query = query.filter(DataRecord.country == country)
    if min_followers:
        query = query.filter(DataRecord.followers_count >= min_followers)
    if max_followers:
        query = query.filter(DataRecord.followers_count <= max_followers)
    if sentiment:
        query = query.filter(DataRecord.sentiment_label == sentiment)
    if keyword:
        query = query.filter(DataRecord.post_content.ilike(f"%{keyword}%"))
    if is_verified is not None:
        query = query.filter(DataRecord.is_verified == is_verified)
    if is_business is not None:
        query = query.filter(DataRecord.is_business_account == is_business)

    return query.offset(skip).limit(limit).all()


@router.get("/{record_id}", response_model=DataRecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific data record."""
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/export")
def export_records(
    export_request: DataExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export filtered data records."""
    # Build query from filters
    query = db.query(DataRecord)
    filters = export_request.filter

    if filters.platforms:
        query = query.filter(DataRecord.platform.in_(filters.platforms))
    if filters.countries:
        query = query.filter(DataRecord.country.in_(filters.countries))
    if filters.min_followers:
        query = query.filter(DataRecord.followers_count >= filters.min_followers)
    if filters.max_followers:
        query = query.filter(DataRecord.followers_count <= filters.max_followers)
    if filters.sentiment:
        query = query.filter(DataRecord.sentiment_label == filters.sentiment)
    if filters.date_from:
        query = query.filter(DataRecord.posted_at >= filters.date_from)
    if filters.date_to:
        query = query.filter(DataRecord.posted_at <= filters.date_to)

    records = query.all()

    # Export
    result = export_data(records, export_request.format, export_request.include_raw)

    logger.info(
        "Data export completed",
        user_id=current_user.id,
        format=export_request.format,
        record_count=len(records)
    )

    return {
        "message": "Export completed",
        "format": export_request.format,
        "record_count": len(records),
        "file_url": result.get("file_url"),
        "file_size": result.get("file_size")
    }


@router.get("/stats/overview")
def get_record_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get data record statistics."""
    total_records = db.query(DataRecord).count()

    platform_stats = db.query(
        DataRecord.platform,
        func.count(DataRecord.id).label("count")
    ).group_by(DataRecord.platform).all()

    sentiment_stats = db.query(
        DataRecord.sentiment_label,
        func.count(DataRecord.id).label("count")
    ).group_by(DataRecord.sentiment_label).all()

    country_stats = db.query(
        DataRecord.country,
        func.count(DataRecord.id).label("count")
    ).group_by(DataRecord.country).order_by(func.count(DataRecord.id).desc()).limit(10).all()

    return {
        "total_records": total_records,
        "platforms": {p: c for p, c in platform_stats},
        "sentiment_distribution": {s: c for s, c in sentiment_stats},
        "top_countries": {c: count for c, count in country_stats}
    }
