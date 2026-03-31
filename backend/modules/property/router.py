"""Property Management module API Router."""

from fastapi import APIRouter

router = APIRouter(prefix="/property", tags=["Property Management"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "property"}
