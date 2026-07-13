"""Proxy management model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, Float, BigInteger
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class ProxyStatus(PyEnum):
    """Proxy health status."""
    ACTIVE = "active"
    SLOW = "slow"
    BANNED = "banned"
    DEAD = "dead"
    ROTATING = "rotating"


class ProxyType(PyEnum):
    """Type of proxy."""
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    ISP = "isp"


class Proxy(Base, TimestampMixin):
    """Proxy server for scraping."""
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)

    # Connection
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    protocol = Column(String(10), default="http")  # http, https, socks5

    # Classification
    proxy_type = Column(Enum(ProxyType), default=ProxyType.RESIDENTIAL)
    country = Column(String(100), index=True)
    city = Column(String(100))
    isp = Column(String(255))

    # Status
    status = Column(Enum(ProxyStatus), default=ProxyStatus.ACTIVE)

    # Performance
    avg_response_time_ms = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)
    total_requests = Column(BigInteger, default=0)
    failed_requests = Column(BigInteger, default=0)

    # Usage
    current_platform = Column(String(50))
    last_used_at = Column(DateTime)
    cooldown_until = Column(DateTime)

    # Metadata
    provider = Column(String(100))  # BrightData, Oxylabs, etc.
    cost_per_gb = Column(Float, default=0.0)
    notes = Column(Text)
