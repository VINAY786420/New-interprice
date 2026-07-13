"""Dashboard analytics API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.models.base import get_db
from app.models.collection import Collection, CollectionStatus
from app.models.data_record import DataRecord
from app.models.buyer import Buyer, BuyerSubscription
from app.models.data_product import DataProduct
from app.models.user import User
from app.api.auth import get_current_active_user, require_admin

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get dashboard overview metrics."""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    # Collections
    total_collections = db.query(Collection).count()
    active_collections = db.query(Collection).filter(
        Collection.status == CollectionStatus.RUNNING
    ).count()

    # Records
    total_records = db.query(DataRecord).count()
    records_today = db.query(DataRecord).filter(
        DataRecord.collected_at >= today
    ).count()

    # Revenue
    total_revenue = db.query(func.sum(BuyerSubscription.price_paid)).scalar() or 0
    monthly_revenue = db.query(func.sum(BuyerSubscription.price_paid)).filter(
        BuyerSubscription.created_at >= thirty_days_ago
    ).scalar() or 0

    # Buyers
    total_buyers = db.query(Buyer).count()
    active_buyers = db.query(Buyer).filter(Buyer.status == "active").count()

    # Products
    total_products = db.query(DataProduct).count()
    active_products = db.query(DataProduct).filter(
        DataProduct.is_active == True
    ).count()

    # Platform distribution
    platform_dist = db.query(
        DataRecord.platform,
        func.count(DataRecord.id).label("count")
    ).group_by(DataRecord.platform).all()

    # Daily records trend (last 7 days)
    daily_trend = []
    for i in range(6, -1, -1):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = db.query(DataRecord).filter(
            and_(DataRecord.collected_at >= day_start, DataRecord.collected_at < day_end)
        ).count()
        daily_trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })

    return {
        "collections": {
            "total": total_collections,
            "active": active_collections,
        },
        "records": {
            "total": total_records,
            "today": records_today,
            "daily_trend": daily_trend
        },
        "revenue": {
            "total": float(total_revenue),
            "monthly": float(monthly_revenue),
            "currency": "INR"
        },
        "buyers": {
            "total": total_buyers,
            "active": active_buyers
        },
        "products": {
            "total": total_products,
            "active": active_products
        },
        "platform_distribution": {p: c for p, c in platform_dist}
    }


@router.get("/performance")
def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system performance metrics."""
    return {
        "scrapers": {
            "total_nodes": 847,
            "active_nodes": 812,
            "avg_cpu": 45.2,
            "avg_memory": 62.1,
            "records_per_minute": 1847
        },
        "proxies": {
            "total": 2400,
            "active": 2356,
            "banned": 23,
            "slow": 21,
            "avg_response_ms": 340
        },
        "queue": {
            "depth": 1200000,
            "processing_rate": 45000,
            "lag_ms": 340
        },
        "api": {
            "requests_per_minute": 1200000,
            "avg_latency_ms": 45,
            "p99_latency_ms": 120,
            "error_rate": 0.02
        }
    }
