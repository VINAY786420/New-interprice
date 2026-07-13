"""Data product model for monetization."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, ForeignKey, Float, Text, BigInteger
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class DataProductType(PyEnum):
    """Types of data products."""
    B2B_LEADS = "b2b_leads"
    SENTIMENT_DATASET = "sentiment_dataset"
    INFLUENCER_DB = "influencer_db"
    TREND_REPORT = "trend_report"
    API_STREAM = "api_stream"
    CUSTOM = "custom"


class DataProduct(Base, TimestampMixin):
    """Marketplace data product."""
    __tablename__ = "data_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    product_type = Column(Enum(DataProductType), nullable=False)

    # Pricing
    price_per_record = Column(Float, default=0.0)
    price_flat = Column(Float, default=0.0)
    price_monthly = Column(Float, default=0.0)
    currency = Column(String(3), default="INR")

    # Data specification
    platforms = Column(JSON)
    data_fields = Column(JSON)
    min_records = Column(BigInteger, default=1000)
    sample_data = Column(JSON)

    # Filters
    filters = Column(JSON)

    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    # Sales
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)

    # Relationships
    subscriptions = relationship("BuyerSubscription", back_populates="product")
