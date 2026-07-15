from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.requests import AuditRequest, EditedPackReviewRequest, LessonRequest, MaterialsRequest
from app.services.generation import generate_teaching_pack_events
from app.services.materials import generate_materials_events
from app.services.audit import audit_material_events, review_edited_pack_events
from app.services.coverage import coverage_overview
from app.core.config import settings
from app.models.coverage import CoverageOverview

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


@router.post("/review-edits")
async def review_edits(request: EditedPackReviewRequest) -> StreamingResponse:
    return StreamingResponse(review_edited_pack_events(request), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/coverage", response_model=CoverageOverview)
async def coverage(session_id: str = Query(min_length=8, max_length=120), subject: str = Query(min_length=1), grade_level: str = Query(min_length=1)) -> CoverageOverview:
    try:
        return coverage_overview(database_path=settings.coverage_db_path, session_id=session_id, subject=subject, grade_level=grade_level)
    except Exception as error:
        raise HTTPException(status_code=503, detail="No fue posible consultar la cobertura curricular local.") from error
