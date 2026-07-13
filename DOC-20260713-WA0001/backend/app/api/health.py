"""Health check API endpoints."""
from fastapi import APIRouter
from sqlalchemy import text
from app.models.base import SessionLocal
import redis
from app.core.config import settings

router = APIRouter()


@router.get("/")
def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "social-data-vault"}


@router.get("/ready")
def readiness_check():
    """Readiness probe for Kubernetes."""
    checks = {}

    # Database check
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Redis check
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks
    }


@router.get("/live")
def liveness_check():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}
