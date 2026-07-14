"""Marketplace Pydantic schemas."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


# ==================== CATEGORY SCHEMAS ====================

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PRODUCT SCHEMAS ====================

class ProductBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    compare_price: Optional[float] = 0
    currency: str = "INR"
    data_format: str = "csv"
    data_platforms: List[str] = []
    data_count: int = 0
    data_sample: Optional[Dict[str, Any]] = None
    data_schema: Optional[Dict[str, Any]] = None
    keywords: List[str] = []
    industries: List[str] = []
    locations: List[str] = []
    category_ids: List[int] = []


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[float] = None
    compare_price: Optional[float] = None
    data_format: Optional[str] = None
    data_platforms: Optional[List[str]] = None
    data_count: Optional[int] = None
    keywords: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    slug: str
    seller_id: int
    status: str
    is_featured: bool
    view_count: int
    purchase_count: int
    rating: float
    review_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int


# ==================== CART SCHEMAS ====================

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_price: float
    quantity: int
    total: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
    item_count: int


# ==================== ORDER SCHEMAS ====================

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    quantity: int
    unit_price: float
    total_price: float
    product_data_format: str
    product_platforms: List[str]
    download_url: Optional[str]
    api_endpoint: Optional[str]

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    subtotal: float
    tax: float
    discount: float
    total: float
    currency: str
    status: str
    payment_status: str
    payment_method: Optional[str]
    download_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    items: List[OrderResponse]
    total: int
    skip: int
    limit: int


class OrderCreate(BaseModel):
    cart_items: List[int]  # Cart item IDs
    payment_method: str = "card"


# ==================== REVIEW SCHEMAS ====================

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    title: Optional[str]
    content: Optional[str]
    is_verified_purchase: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== API KEY SCHEMAS ====================

class APIKeyCreate(BaseModel):
    product_id: int
    name: Optional[str] = "Default"


class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    rate_limit: int
    monthly_limit: int
    requests_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
