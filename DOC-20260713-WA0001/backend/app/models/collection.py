"""Data collection job model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class CollectionStatus(PyEnum):
    """Status of a data collection job."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Collection(Base, TimestampMixin):
    """Data collection job configuration and status."""
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration
    platforms = Column(JSON, nullable=False)  # ["twitter", "instagram"]
    keywords = Column(JSON, nullable=False)    # ["#marketing", "fitness"]
    data_fields = Column(JSON, nullable=False) # ["username", "followers", "sentiment"]
    filters = Column(JSON, default=dict)       # {"location": "India", "min_followers": 1000}

    # Targets
    volume_target = Column(BigInteger, default=10000)
    volume_collected = Column(BigInteger, default=0)

    # Scheduling
    schedule_type = Column(String(50), default="once")  # once, hourly, daily, weekly
    cron_expression = Column(String(100))
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)

    # Status
    status = Column(Enum(CollectionStatus), default=CollectionStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    # Performance
    records_per_minute = Column(Integer, default=0)
    estimated_completion = Column(DateTime)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="collections")

    # Relationships
    records = relationship("DataRecord", back_populates="collection")
    scraper_nodes = relationship("ScraperNode", back_populates="collection")
