"""School Management module API Router."""

from fastapi import APIRouter

router = APIRouter(prefix="/school", tags=["School Management"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "school"}
