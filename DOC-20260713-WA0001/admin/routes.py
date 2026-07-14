"""Admin dashboard API routes."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.db.session import get_db
from app.core.auth import get_current_user, get_current_active_user
from app.models.user import User
from app.models.marketplace import (
    Product, Category, Order, OrderItem, Review, APIKey,
    ProductStatus, OrderStatus, PaymentStatus
)
from app.core.logging import logger

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Dependency to check admin access."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    period: str = Query("7d", regex="^(24h|7d|30d|90d|1y)$"),
):
    """Get real-time dashboard statistics."""

    # Calculate date range
    period_map = {
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    start_date = datetime.utcnow() - period_map.get(period, timedelta(days=7))

    # User stats
    total_users = db.query(func.count(User.id)).scalar()
    new_users = db.query(func.count(User.id)).filter(User.created_at >= start_date).scalar()
    active_users = db.query(func.count(User.id)).filter(
        User.last_login >= start_date
    ).scalar()

    # Product stats
    total_products = db.query(func.count(Product.id)).scalar()
    pending_products = db.query(func.count(Product.id)).filter(
        Product.status == ProductStatus.PENDING_REVIEW
    ).scalar()
    active_products = db.query(func.count(Product.id)).filter(
        Product.status == ProductStatus.ACTIVE
    ).scalar()
    featured_products = db.query(func.count(Product.id)).filter(
        Product.is_featured == True
    ).scalar()

    # Order stats
    total_orders = db.query(func.count(Order.id)).filter(Order.created_at >= start_date).scalar()
    total_revenue = db.query(func.sum(Order.total)).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID,
    ).scalar() or 0

    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.PENDING
    ).scalar()
    completed_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.COMPLETED
    ).scalar()

    # API usage
    total_api_requests = db.query(func.sum(APIKey.requests_count)).scalar() or 0
    active_api_keys = db.query(func.count(APIKey.id)).filter(
        APIKey.is_active == True
    ).scalar()

    # Top selling products
    top_products = db.query(
        Product.id,
        Product.title,
        Product.price,
        func.sum(OrderItem.quantity).label("total_sales"),
        func.sum(OrderItem.total_price).label("total_revenue"),
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID,
    ).group_by(Product.id).order_by(desc("total_sales")).limit(10).all()

    # Sales chart data (daily)
    sales_data = db.query(
        func.date(Order.created_at).label("date"),
        func.count(Order.id).label("orders"),
        func.coalesce(func.sum(Order.total), 0).label("revenue"),
    ).filter(
        Order.created_at >= start_date,
    ).group_by(func.date(Order.created_at)).order_by("date").all()

    return {
        "period": period,
        "users": {
            "total": total_users,
            "new": new_users,
            "active": active_users,
        },
        "products": {
            "total": total_products,
            "pending_review": pending_products,
            "active": active_products,
            "featured": featured_products,
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "completed": completed_orders,
            "revenue": round(total_revenue, 2),
        },
        "api": {
            "total_requests": total_api_requests,
            "active_keys": active_api_keys,
        },
        "top_products": [
            {
                "id": p.id,
                "title": p.title,
                "price": p.price,
                "sales": p.total_sales,
                "revenue": round(p.total_revenue, 2),
            }
            for p in top_products
        ],
        "sales_chart": [
            {
                "date": str(s.date),
                "orders": s.orders,
                "revenue": round(float(s.revenue), 2),
            }
            for s in sales_data
        ],
    }


# ==================== USER MANAGEMENT ====================

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_seller: Optional[bool] = None,
):
    """List all users."""
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_seller is not None:
        query = query.filter(User.is_seller == is_seller)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": users,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    db.commit()
    return {"message": "User updated"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# ==================== PRODUCT MANAGEMENT ====================

@router.get("/products/pending")
def get_pending_products(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 20,
):
    """Get products pending review."""
    query = db.query(Product).filter(Product.status == ProductStatus.PENDING_REVIEW)
    total = query.count()
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": products,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/products/{product_id}/approve")
def approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Approve a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = ProductStatus.ACTIVE
    product.published_at = datetime.utcnow()
    db.commit()

    # TODO: Send notification to seller

    return {"message": "Product approved", "product_id": product_id}


@router.post("/products/{product_id}/reject")
def reject_product(
    product_id: int,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Reject a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = ProductStatus.REJECTED
    db.commit()

    # TODO: Send notification to seller with reason

    return {"message": "Product rejected", "reason": reason}


@router.post("/products/{product_id}/feature")
def feature_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Toggle featured status."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_featured = not product.is_featured
    db.commit()

    return {
        "message": f"Product {'featured' if product.is_featured else 'unfeatured'}",
        "is_featured": product.is_featured,
    }


# ==================== ORDER MANAGEMENT ====================

@router.get("/orders")
def list_all_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all orders."""
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": orders,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    if status == OrderStatus.COMPLETED:
        order.completed_at = datetime.utcnow()

    db.commit()
    return {"message": "Order status updated", "status": status}


# ==================== REVIEW MODERATION ====================

@router.get("/reviews/pending")
def get_pending_reviews(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
):
    """Get reviews pending approval."""
    query = db.query(Review).filter(Review.is_approved == False)
    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": reviews,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/reviews/{review_id}/approve")
def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Approve a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_approved = True
    db.commit()

    # Update product rating
    product = review.product
    reviews = db.query(Review).filter(
        Review.product_id == product.id,
        Review.is_approved == True,
    ).all()

    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        product.rating = round(avg_rating, 1)
        product.review_count = len(reviews)
        db.commit()

    return {"message": "Review approved"}


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}


# ==================== PLATFORM ANALYTICS ====================

@router.get("/analytics/platforms")
def get_platform_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
):
    """Get analytics by platform."""
    period_map = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    start_date = datetime.utcnow() - period_map.get(period, timedelta(days=30))

    # Get all products with their platforms
    products = db.query(Product).filter(
        Product.status == ProductStatus.ACTIVE
    ).all()

    platform_stats = {}

    for product in products:
        for platform in product.data_platforms or []:
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "product_count": 0,
                    "total_sales": 0,
                    "total_revenue": 0,
                }

            platform_stats[platform]["product_count"] += 1

    # Get sales by platform
    sales_by_platform = db.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label("sales"),
        func.sum(OrderItem.total_price).label("revenue"),
    ).join(Order).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID,
    ).group_by(OrderItem.product_id).all()

    for sale in sales_by_platform:
        product = db.query(Product).filter(Product.id == sale.product_id).first()
        if product and product.data_platforms:
            for platform in product.data_platforms:
                if platform in platform_stats:
                    platform_stats[platform]["total_sales"] += sale.sales
                    platform_stats[platform]["total_revenue"] += float(sale.revenue)

    return {
        "period": period,
        "platforms": [
            {
                "name": platform,
                "product_count": stats["product_count"],
                "total_sales": stats["total_sales"],
                "total_revenue": round(stats["total_revenue"], 2),
            }
            for platform, stats in platform_stats.items()
        ],
    }


@router.get("/analytics/revenue")
def get_revenue_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
):
    """Get detailed revenue analytics."""
    period_map = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    start_date = datetime.utcnow() - period_map.get(period, timedelta(days=30))

    # Daily revenue
    daily = db.query(
        func.date(Order.created_at).label("date"),
        func.count(Order.id).label("orders"),
        func.coalesce(func.sum(Order.subtotal), 0).label("subtotal"),
        func.coalesce(func.sum(Order.tax), 0).label("tax"),
        func.coalesce(func.sum(Order.total), 0).label("total"),
    ).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID,
    ).group_by(func.date(Order.created_at)).order_by("date").all()

    # Revenue by category
    category_revenue = db.query(
        Category.name,
        func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"),
        func.count(OrderItem.id).label("sales"),
    ).join(Product, Category.products).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID,
    ).group_by(Category.id).all()

    return {
        "period": period,
        "daily": [
            {
                "date": str(d.date),
                "orders": d.orders,
                "subtotal": round(float(d.subtotal), 2),
                "tax": round(float(d.tax), 2),
                "total": round(float(d.total), 2),
            }
            for d in daily
        ],
        "by_category": [
            {
                "category": c.name,
                "revenue": round(float(c.revenue), 2),
                "sales": c.sales,
            }
            for c in category_revenue
        ],
    }
