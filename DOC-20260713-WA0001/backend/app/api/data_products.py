"""Data product marketplace API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.base import get_db
from app.models.data_product import DataProduct, DataProductType
from app.models.user import User
from app.schemas.data_product import DataProductCreate, DataProductResponse, DataProductStats
from app.api.auth import get_current_active_user, require_admin
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=DataProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: DataProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new data product."""
    db_product = DataProduct(
        name=product_data.name,
        description=product_data.description,
        product_type=DataProductType(product_data.product_type),
        price_per_record=product_data.price_per_record,
        price_flat=product_data.price_flat,
        price_monthly=product_data.price_monthly,
        currency=product_data.currency,
        platforms=product_data.platforms,
        data_fields=product_data.data_fields,
        min_records=product_data.min_records,
        filters=product_data.filters,
        is_public=product_data.is_public,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    logger.info("Data product created", product_id=db_product.id, name=db_product.name)
    return db_product


@router.get("/", response_model=List[DataProductResponse])
def list_products(
    product_type: str = None,
    is_public: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List available data products."""
    query = db.query(DataProduct).filter(DataProduct.is_active == True)

    if is_public:
        query = query.filter(DataProduct.is_public == True)
    if product_type:
        query = query.filter(DataProduct.product_type == product_type)

    return query.all()


@router.get("/{product_id}", response_model=DataProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific data product."""
    product = db.query(DataProduct).filter(DataProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=DataProductResponse)
def update_product(
    product_id: int,
    product_data: DataProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a data product."""
    product = db.query(DataProduct).filter(DataProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a data product."""
    product = db.query(DataProduct).filter(DataProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return None


@router.get("/stats/overview", response_model=DataProductStats)
def get_product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get data product statistics."""
    from sqlalchemy import func

    total = db.query(DataProduct).count()
    active = db.query(DataProduct).filter(DataProduct.is_active == True).count()
    total_revenue = db.query(func.sum(DataProduct.total_revenue)).scalar() or 0
    total_sales = db.query(func.sum(DataProduct.total_sales)).scalar() or 0

    top_product = db.query(DataProduct).order_by(DataProduct.total_revenue.desc()).first()

    return DataProductStats(
        total_products=total,
        active_products=active,
        total_revenue=float(total_revenue),
        total_sales=int(total_sales),
        top_product=top_product.name if top_product else None
    )
