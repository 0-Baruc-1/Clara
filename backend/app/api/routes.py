from fastapi import APIRouter
from app.models.requests import LessonRequest
from app.models.teaching_pack import TeachingPack
from app.services.generation import generate_teaching_pack

router = APIRouter()

@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@router.post("/generate", response_model=TeachingPack)
async def generate(request: LessonRequest) -> TeachingPack:
    """Generate a teaching pack. Outputs are placeholders for now."""
    return await generate_teaching_pack(request)

