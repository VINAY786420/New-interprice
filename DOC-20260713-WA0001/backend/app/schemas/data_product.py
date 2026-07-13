"""Pydantic schemas for data products."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DataProductType(str, Enum):
    B2B_LEADS = "b2b_leads"
    SENTIMENT_DATASET = "sentiment_dataset"
    INFLUENCER_DB = "influencer_db"
    TREND_REPORT = "trend_report"
    API_STREAM = "api_stream"
    CUSTOM = "custom"


class DataProductCreate(BaseModel):
    """Schema for creating a data product."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    product_type: DataProductType
    price_per_record: float = Field(default=0.0, ge=0)
    price_flat: float = Field(default=0.0, ge=0)
    price_monthly: float = Field(default=0.0, ge=0)
    currency: str = "INR"
    platforms: List[str]
    data_fields: List[str]
    min_records: int = Field(default=1000, ge=100)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_public: bool = False


class DataProductResponse(BaseModel):
    """Schema for data product response."""
    id: int
    name: str
    description: Optional[str]
    product_type: DataProductType
    price_per_record: float
    price_flat: float
    price_monthly: float
    currency: str
    platforms: List[str]
    data_fields: List[str]
    min_records: int
    filters: Dict[str, Any]
    is_active: bool
    is_public: bool
    total_sales: int
    total_revenue: float
    created_at: datetime

    class Config:
        from_attributes = True


class DataProductStats(BaseModel):
    """Data product statistics."""
    total_products: int
    active_products: int
    total_revenue: float
    total_sales: int
    top_product: Optional[str]
