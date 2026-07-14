"""Marketplace API routes."""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.session import get_db
from app.core.auth import get_current_user, get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.marketplace import (
    Product, Category, CartItem, Order, OrderItem, 
    Review, APIKey, ProductStatus, OrderStatus, PaymentStatus, DataFormat
)
from app.schemas.marketplace import (
    ProductCreate, ProductUpdate, ProductResponse, ProductList,
    CategoryCreate, CategoryResponse,
    CartItemCreate, CartResponse,
    OrderCreate, OrderResponse, OrderList,
    ReviewCreate, ReviewResponse,
    APIKeyCreate, APIKeyResponse,
)
from app.services.stripe_service import stripe_service
from app.services.email_service import send_order_confirmation
from app.core.logging import logger

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ==================== CATEGORIES ====================

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    parent_id: Optional[int] = None,
):
    """List all product categories."""
    query = db.query(Category).filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    else:
        query = query.filter(Category.parent_id == None)
    return query.order_by(Category.sort_order).all()


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new category (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# ==================== PRODUCTS ====================

@router.get("/products", response_model=ProductList)
def list_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    platform: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort: str = Query("newest", regex="^(newest|price_asc|price_desc|popular|rating)$"),
    status: ProductStatus = ProductStatus.ACTIVE,
):
    """List marketplace products with filters."""
    query = db.query(Product).filter(Product.status == status)

    if category:
        query = query.join(Product.categories).filter(Category.slug == category)

    if platform:
        query = query.filter(Product.data_platforms.contains([platform]))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if search:
        search_filter = or_(
            Product.title.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
            Product.keywords.contains([search]),
        )
        query = query.filter(search_filter)

    # Sorting
    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "popular": Product.purchase_count.desc(),
        "rating": Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    products = query.offset(skip).limit(limit).all()

    return {
        "items": products,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/products/featured", response_model=List[ProductResponse])
def get_featured_products(
    db: Session = Depends(get_db),
    limit: int = Query(8, ge=1, le=20),
):
    """Get featured products."""
    return db.query(Product).filter(
        Product.is_featured == True,
        Product.status == ProductStatus.ACTIVE,
    ).order_by(Product.created_at.desc()).limit(limit).all()


@router.get("/products/{slug}", response_model=ProductResponse)
def get_product(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get product details by slug."""
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Increment view count
    product.view_count += 1
    db.commit()

    return product


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product listing."""
    # Generate slug
    base_slug = product.title.lower().replace(" ", "-")[:50]
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_product = Product(
        **product.dict(),
        seller_id=current_user.id,
        slug=slug,
        status=ProductStatus.PENDING_REVIEW,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a product."""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if db_product.seller_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product."""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if db_product.seller_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}


# ==================== CART ====================

@router.get("/cart", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get user's cart."""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

    total = sum(item.product.price * item.quantity for item in cart_items)

    return {
        "items": cart_items,
        "total": total,
        "item_count": len(cart_items),
    }


@router.post("/cart/add")
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add item to cart."""
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Product not available")

    # Check if already in cart
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item.product_id,
    ).first()

    if existing:
        existing.quantity += item.quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity,
        )
        db.add(cart_item)

    db.commit()
    return {"message": "Added to cart"}


@router.delete("/cart/{item_id}")
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove item from cart."""
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id,
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()
    return {"message": "Removed from cart"}


@router.delete("/cart/clear")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clear entire cart."""
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}


# ==================== ORDERS & CHECKOUT ====================

@router.post("/checkout", response_model=dict)
def create_checkout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create checkout session from cart."""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    tax = subtotal * 0.18  # 18% GST
    total = subtotal + tax

    # Create order
    order_number = f"SDV-{datetime.now().strftime('%Y%m%d')}-{current_user.id:04d}"

    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(order)
    db.flush()

    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price,
            total_price=cart_item.product.price * cart_item.quantity,
            product_title=cart_item.product.title,
            product_data_format=cart_item.product.data_format.value,
            product_platforms=cart_item.product.data_platforms,
        )
        db.add(order_item)

    # Create Stripe payment intent
    try:
        payment_intent = stripe_service.create_payment_intent(
            amount=int(total * 100),  # Convert to paise
            currency="inr",
            metadata={"order_id": order.id, "order_number": order_number},
        )
        order.stripe_payment_intent_id = payment_intent.id
    except Exception as e:
        logger.error(f"Stripe payment intent creation failed: {e}")
        raise HTTPException(status_code=500, detail="Payment initialization failed")

    db.commit()

    # Clear cart
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()

    return {
        "order_id": order.id,
        "order_number": order_number,
        "client_secret": payment_intent.client_secret,
        "total": total,
    }


@router.post("/orders/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Confirm order after payment."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify payment with Stripe
    try:
        payment_intent = stripe_service.retrieve_payment_intent(order.stripe_payment_intent_id)
        if payment_intent.status == "succeeded":
            order.payment_status = PaymentStatus.PAID
            order.status = OrderStatus.CONFIRMED
            order.completed_at = datetime.utcnow()

            # Generate download URLs and API keys
            for item in order.items:
                product = item.product

                # Generate API key for API products
                if product.data_format == DataFormat.API:
                    api_key = APIKey(
                        user_id=current_user.id,
                        product_id=product.id,
                        key=f"sdv_{current_user.id}_{product.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=f"{product.title} - {order.order_number}",
                        expires_at=datetime.utcnow() + timedelta(days=30),
                    )
                    db.add(api_key)
                    item.api_endpoint = f"/api/v1/data/{product.slug}"

                # Generate download URL for file products
                else:
                    item.download_url = f"/api/v1/downloads/{order.order_number}/{item.id}"

                # Update product stats
                product.purchase_count += 1

            db.commit()

            # Send confirmation email
            send_order_confirmation(current_user.email, order)

            return {
                "message": "Order confirmed",
                "order": order,
            }
        else:
            raise HTTPException(status_code=400, detail="Payment not completed")

    except Exception as e:
        logger.error(f"Order confirmation failed: {e}")
        raise HTTPException(status_code=500, detail="Order confirmation failed")


@router.get("/orders", response_model=OrderList)
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 20,
):
    """List user's orders."""
    query = db.query(Order).filter(Order.user_id == current_user.id)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": orders,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get order details."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.get("/orders/{order_id}/download")
def download_order(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download purchased data."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not completed")

    item = db.query(OrderItem).filter(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    # Generate and stream the data file
    # This would connect to your data storage (S3, etc.)
    # For now, return a placeholder
    return {"download_url": item.download_url}


# ==================== REVIEWS ====================

@router.post("/products/{product_id}/reviews", response_model=ReviewResponse)
def create_review(
    product_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a product review."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if user purchased this product
    has_purchased = db.query(Order).join(OrderItem).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.COMPLETED,
    ).first()

    db_review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=review.rating,
        title=review.title,
        content=review.content,
        is_verified_purchase=bool(has_purchased),
    )
    db.add(db_review)

    # Update product rating
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else review.rating
    product.rating = round(avg_rating, 1)
    product.review_count = len(reviews)

    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/products/{product_id}/reviews", response_model=List[ReviewResponse])
def list_reviews(
    product_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    """List product reviews."""
    return db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_approved == True,
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()


# ==================== API KEYS ====================

@router.get("/api-keys", response_model=List[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List user's API keys."""
    return db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True,
    ).all()


@router.post("/api-keys/{key_id}/regenerate")
def regenerate_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Regenerate an API key."""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id,
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.key = f"sdv_{current_user.id}_{api_key.product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    api_key.requests_count = 0
    db.commit()

    return {"api_key": api_key.key}


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke an API key."""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id,
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    db.commit()
    return {"message": "API key revoked"}
