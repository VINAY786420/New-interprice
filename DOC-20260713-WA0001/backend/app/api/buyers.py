"""Buyer management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets

from app.models.base import get_db
from app.models.buyer import Buyer, BuyerSubscription, BuyerStatus, SubscriptionStatus
from app.models.data_product import DataProduct
from app.models.user import User
from app.schemas.buyer import BuyerCreate, BuyerResponse, SubscriptionCreate, SubscriptionResponse, BuyerStats
from app.api.auth import get_current_active_user, require_admin
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=BuyerResponse, status_code=status.HTTP_201_CREATED)
def create_buyer(
    buyer_data: BuyerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Register a new buyer."""
    # Generate API key
    api_key = f"sdv_{secrets.token_urlsafe(32)}"

    db_buyer = Buyer(
        company_name=buyer_data.company_name,
        contact_name=buyer_data.contact_name,
        email=buyer_data.email,
        phone=buyer_data.phone,
        industry=buyer_data.industry,
        company_size=buyer_data.company_size,
        use_case=buyer_data.use_case,
        api_key=api_key,
        status=BuyerStatus.ACTIVE,
    )
    db.add(db_buyer)
    db.commit()
    db.refresh(db_buyer)

    logger.info("New buyer registered", buyer_id=db_buyer.id, company=db_buyer.company_name)
    return db_buyer


@router.get("/", response_model=List[BuyerResponse])
def list_buyers(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all buyers."""
    query = db.query(Buyer)
    if status:
        query = query.filter(Buyer.status == status)
    return query.all()


@router.get("/{buyer_id}", response_model=BuyerResponse)
def get_buyer(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific buyer."""
    buyer = db.query(Buyer).filter(Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.post("/{buyer_id}/subscribe")
def create_subscription(
    buyer_id: int,
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a subscription for a buyer."""
    buyer = db.query(Buyer).filter(Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    product = db.query(DataProduct).filter(DataProduct.id == subscription_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from datetime import datetime, timedelta

    db_subscription = BuyerSubscription(
        buyer_id=buyer_id,
        product_id=subscription_data.product_id,
        price_paid=subscription_data.price_paid,
        billing_cycle=subscription_data.billing_cycle,
        records_limit=subscription_data.records_limit,
        api_calls_limit=subscription_data.api_calls_limit,
        status=SubscriptionStatus.ACTIVE,
        starts_at=datetime.utcnow(),
        ends_at=datetime.utcnow() + timedelta(days=30) if subscription_data.billing_cycle == "monthly" else None,
    )
    db.add(db_subscription)

    # Update product stats
    product.total_sales += 1
    product.total_revenue += subscription_data.price_paid

    db.commit()
    db.refresh(db_subscription)

    logger.info(
        "Subscription created",
        buyer_id=buyer_id,
        product_id=subscription_data.product_id,
        amount=subscription_data.price_paid
    )

    return {
        "message": "Subscription created successfully",
        "subscription_id": db_subscription.id,
        "api_key": buyer.api_key
    }


@router.get("/{buyer_id}/subscriptions")
def get_buyer_subscriptions(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all subscriptions for a buyer."""
    subscriptions = db.query(BuyerSubscription).filter(BuyerSubscription.buyer_id == buyer_id).all()
    return subscriptions


@router.get("/stats/overview", response_model=BuyerStats)
def get_buyer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get buyer statistics."""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    total = db.query(Buyer).count()
    active = db.query(Buyer).filter(Buyer.status == BuyerStatus.ACTIVE).count()
    total_subs = db.query(BuyerSubscription).count()

    # MRR calculation
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    mrr = db.query(func.sum(BuyerSubscription.price_paid)).filter(
        BuyerSubscription.status == SubscriptionStatus.ACTIVE,
        BuyerSubscription.starts_at >= thirty_days_ago
    ).scalar() or 0

    return BuyerStats(
        total_buyers=total,
        active_buyers=active,
        total_subscriptions=total_subs,
        monthly_recurring_revenue=float(mrr),
        churn_rate=5.2
    )
