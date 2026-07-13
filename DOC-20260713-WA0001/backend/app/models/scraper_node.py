"""Scraper node management."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, ForeignKey, Float, BigInteger, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class NodeStatus(PyEnum):
    """Scraper node status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    TERMINATED = "terminated"


class ScraperNode(Base, TimestampMixin):
    """Individual scraper worker node."""
    __tablename__ = "scraper_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, index=True)  # UUID
    name = Column(String(255))

    # Hardware
    ip_address = Column(String(50))
    region = Column(String(100))
    instance_type = Column(String(50))

    # Status
    status = Column(Enum(NodeStatus), default=NodeStatus.IDLE)

    # Performance
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    disk_usage = Column(Float, default=0.0)

    # Metrics
    records_collected = Column(BigInteger, default=0)
    requests_made = Column(BigInteger, default=0)
    errors_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0.0)

    # Current job
    current_platform = Column(String(50))
    current_keyword = Column(String(255))
    started_at = Column(DateTime)

    # Error tracking
    last_error = Column(Text)
    last_error_at = Column(DateTime)

    # Relationships
    collection_id = Column(Integer, ForeignKey("collections.id"))
    collection = relationship("Collection", back_populates="scraper_nodes")
