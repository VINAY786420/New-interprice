"""Pydantic schemas for collection jobs."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CollectionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollectionCreate(BaseModel):
    """Schema for creating a collection job."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    platforms: List[str] = Field(..., min_length=1)
    keywords: List[str] = Field(..., min_length=1)
    data_fields: List[str] = Field(default=["username", "followers", "engagement"])
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    volume_target: int = Field(default=10000, ge=100, le=10000000)
    schedule_type: str = "once"
    cron_expression: Optional[str] = None


class CollectionUpdate(BaseModel):
    """Schema for updating a collection job."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CollectionStatus] = None
    volume_target: Optional[int] = None


class CollectionResponse(BaseModel):
    """Schema for collection job response."""
    id: int
    name: str
    description: Optional[str]
    platforms: List[str]
    keywords: List[str]
    data_fields: List[str]
    filters: Dict[str, Any]
    volume_target: int
    volume_collected: int
    schedule_type: str
    status: CollectionStatus
    progress_percent: int
    records_per_minute: int
    estimated_completion: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CollectionStats(BaseModel):
    """Collection statistics."""
    total_collections: int
    active_collections: int
    total_records_collected: int
    avg_collection_time_minutes: float
    success_rate: float
