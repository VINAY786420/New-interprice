"""Marketplace database models."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, ForeignKey, Enum, JSON, Index, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProductStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    REJECTED = "rejected"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class DataFormat(str, PyEnum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    API = "api"
    SQL = "sql"


# Association table for product categories
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class Category(Base):
    """Product category."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(255))
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", secondary=product_categories, back_populates="categories")


class Product(Base):
    """Marketplace product (data package)."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic info
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    short_description = Column(String(500))

    # Pricing
    price = Column(Float, nullable=False)
    compare_price = Column(Float, default=0)
    currency = Column(String(3), default="INR")

    # Data specifics
    data_format = Column(Enum(DataFormat), default=DataFormat.CSV)
    data_platforms = Column(JSON, default=list)  # ["twitter", "reddit", "linkedin"]
    data_count = Column(Integer, default=0)  # Number of records
    data_sample = Column(JSON, default=dict)  # Sample data preview
    data_schema = Column(JSON, default=dict)  # Column definitions

    # Filters/tags
    keywords = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    locations = Column(JSON, default=list)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)

    # Status
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT)
    is_featured = Column(Boolean, default=False)

    # Stats
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    seller = relationship("User", back_populates="products")
    categories = relationship("Category", secondary=product_categories, back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    api_keys = relationship("APIKey", back_populates="product")

    __table_args__ = (
        Index("idx_product_status", "status"),
        Index("idx_product_price", "price"),
        Index("idx_product_featured", "is_featured"),
    )


class CartItem(Base):
    """Shopping cart item."""
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")


class Order(Base):
    """Customer order."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Pricing
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0)
    discount = Column(Float, default=0)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")

    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Payment
    payment_method = Column(String(50))
    payment_id = Column(String(255))
    stripe_payment_intent_id = Column(String(255))

    # Delivery
    download_url = Column(String(500))
    api_key = Column(String(255))
    expires_at = Column(DateTime(timezone=True))

    # Notes
    buyer_notes = Column(Text)
    seller_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Order line item."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Product snapshot
    product_title = Column(String(255))
    product_data_format = Column(String(20))
    product_platforms = Column(JSON)

    # Delivery
    download_url = Column(String(500))
    api_endpoint = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Review(Base):
    """Product review."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255))
    content = Column(Text)

    is_verified_purchase = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class APIKey(Base):
    """API key for data access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    key = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))

    # Limits
    rate_limit = Column(Integer, default=1000)  # requests per hour
    monthly_limit = Column(Integer, default=10000)

    # Usage
    requests_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="api_keys")
    product = relationship("Product", back_populates="api_keys")
