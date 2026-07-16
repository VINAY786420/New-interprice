from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/status", tags=["health"])
def status():
    return {"status": "ok"}
