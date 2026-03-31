"""eLearning module API Router."""

from fastapi import APIRouter

router = APIRouter(prefix="/elearning", tags=["eLearning"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "elearning"}
