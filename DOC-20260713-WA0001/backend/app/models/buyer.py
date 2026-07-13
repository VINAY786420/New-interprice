"""Buyer and subscription models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class BuyerStatus(PyEnum):
    """Buyer account status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionStatus(PyEnum):
    """Subscription status."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Buyer(Base, TimestampMixin):
    """Buyer/Client organization."""
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))

    # Business
    industry = Column(String(100))
    company_size = Column(String(50))
    use_case = Column(Text)

    # Status
    status = Column(Enum(BuyerStatus), default=BuyerStatus.PENDING)

    # API Access
    api_key = Column(String(255), unique=True, index=True)
    api_calls_today = Column(Integer, default=0)
    api_calls_limit = Column(Integer, default=10000)
    rate_limit_per_minute = Column(Integer, default=60)

    # Billing
    stripe_customer_id = Column(String(255))
    billing_address = Column(JSON)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="buyer_profile")
    subscriptions = relationship("BuyerSubscription", back_populates="buyer")


class BuyerSubscription(Base, TimestampMixin):
    """Buyer subscription to a data product."""
    __tablename__ = "buyer_subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # Pricing
    price_paid = Column(Float, nullable=False)
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly, one-time

    # Usage
    records_delivered = Column(Integer, default=0)
    records_limit = Column(Integer)
    api_calls_used = Column(Integer, default=0)
    api_calls_limit = Column(Integer)

    # Status
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)

    # Stripe
    stripe_subscription_id = Column(String(255))
    stripe_payment_intent_id = Column(String(255))

    # Relationships
    buyer_id = Column(Integer, ForeignKey("buyers.id"))
    buyer = relationship("Buyer", back_populates="subscriptions")

    product_id = Column(Integer, ForeignKey("data_products.id"))
    product = relationship("DataProduct", back_populates="subscriptions")
