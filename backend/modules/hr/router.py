"""HR module API Router."""

from fastapi import APIRouter

router = APIRouter(prefix="/hr", tags=["Human Resources"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "hr"}
