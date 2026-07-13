"""Pydantic schemas for data records."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DataRecordResponse(BaseModel):
    """Schema for data record response."""
    id: int
    platform: str
    username: str
    display_name: Optional[str]
    followers_count: int
    following_count: int
    posts_count: int
    engagement_rate: Optional[float]
    post_content: Optional[str]
    hashtags: Optional[List[str]]
    likes_count: int
    comments_count: int
    shares_count: int
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    country: Optional[str]
    city: Optional[str]
    interests: Optional[List[str]]
    posted_at: Optional[datetime]
    collected_at: datetime
    is_verified: bool
    is_business_account: bool

    class Config:
        from_attributes = True


class DataRecordFilter(BaseModel):
    """Filter schema for data records."""
    platforms: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    sentiment: Optional[str] = None
    keywords: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_verified: Optional[bool] = None
    is_business_account: Optional[bool] = None
    limit: int = 100
    offset: int = 0


class DataExportRequest(BaseModel):
    """Schema for data export request."""
    filter: DataRecordFilter
    format: str = "csv"  # csv, json, excel, sql
    include_raw: bool = False
    email_delivery: Optional[str] = None
