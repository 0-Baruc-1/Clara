from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.requests import AuditRequest, LessonRequest, MaterialsRequest
from app.services.generation import generate_teaching_pack_events
from app.services.materials import generate_materials_events
from app.services.audit import audit_material_events

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/generate")
async def generate(request: LessonRequest) -> StreamingResponse:
    """Stream validated Planner and Designer milestones as SSE frames."""
    return StreamingResponse(
        generate_teaching_pack_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.post("/generate-materials")
async def generate_materials(request: MaterialsRequest) -> StreamingResponse:
    return StreamingResponse(generate_materials_events(request), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.post("/audit")
async def audit_material(request: AuditRequest) -> StreamingResponse:
    return StreamingResponse(audit_material_events(request), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
