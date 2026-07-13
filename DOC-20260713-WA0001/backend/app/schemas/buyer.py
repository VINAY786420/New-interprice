"""Pydantic schemas for buyer management."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BuyerStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BuyerCreate(BaseModel):
    """Schema for creating a buyer."""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    use_case: Optional[str] = None


class BuyerResponse(BaseModel):
    """Schema for buyer response."""
    id: int
    company_name: str
    contact_name: Optional[str]
    email: str
    phone: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    status: BuyerStatus
    api_key: str
    api_calls_today: int
    api_calls_limit: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""
    product_id: int
    buyer_id: int
    price_paid: float = Field(..., gt=0)
    billing_cycle: str = "monthly"
    records_limit: Optional[int] = None
    api_calls_limit: Optional[int] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: int
    price_paid: float
    billing_cycle: str
    records_delivered: int
    records_limit: Optional[int]
    api_calls_used: int
    api_calls_limit: Optional[int]
    status: SubscriptionStatus
    starts_at: datetime
    ends_at: Optional[datetime]
    product_name: str
    buyer_company: str

    class Config:
        from_attributes = True


class BuyerStats(BaseModel):
    """Buyer statistics."""
    total_buyers: int
    active_buyers: int
    total_subscriptions: int
    monthly_recurring_revenue: float
    churn_rate: float
