from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.requests import AuditRequest, EditedPackReviewRequest, LessonRequest, MaterialsRequest
from app.services.generation import generate_teaching_pack_events
from app.services.materials import generate_materials_events
from app.services.audit import audit_material_events, review_edited_pack_events
from app.services.coverage import coverage_overview
from app.core.config import settings
from app.models.coverage import CoverageOverview

router = APIRouter()


def request_api_key(value: str | None) -> str | None:
    """Keep a user-supplied key ephemeral and reject oversized headers without echoing it."""
    key = value.strip() if value else None
    if key and len(key) > 512:
        raise HTTPException(status_code=400, detail="La clave proporcionada no tiene un formato válido.")
    return key


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/generate")
async def generate(request: LessonRequest, x_clara_openai_key: Annotated[str | None, Header(alias="X-Clara-OpenAI-Key")] = None) -> StreamingResponse:
    """Stream the reviewed Planner → Designer → Assessment pipeline as SSE frames."""
    return StreamingResponse(
        generate_teaching_pack_events(request, api_key=request_api_key(x_clara_openai_key)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.post("/generate-materials")
async def generate_materials(request: MaterialsRequest, x_clara_openai_key: Annotated[str | None, Header(alias="X-Clara-OpenAI-Key")] = None) -> StreamingResponse:
    return StreamingResponse(generate_materials_events(request, api_key=request_api_key(x_clara_openai_key)), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.post("/audit")
async def audit_material(request: AuditRequest, x_clara_openai_key: Annotated[str | None, Header(alias="X-Clara-OpenAI-Key")] = None) -> StreamingResponse:
    return StreamingResponse(audit_material_events(request, api_key=request_api_key(x_clara_openai_key)), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/review-edits")
async def review_edits(request: EditedPackReviewRequest, x_clara_openai_key: Annotated[str | None, Header(alias="X-Clara-OpenAI-Key")] = None) -> StreamingResponse:
    return StreamingResponse(review_edited_pack_events(request, api_key=request_api_key(x_clara_openai_key)), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/coverage", response_model=CoverageOverview)
async def coverage(session_id: str = Query(min_length=8, max_length=120), subject: str = Query(min_length=1), grade_level: str = Query(min_length=1)) -> CoverageOverview:
    try:
        return coverage_overview(database_path=settings.coverage_db_path, session_id=session_id, subject=subject, grade_level=grade_level)
    except Exception as error:
        raise HTTPException(status_code=503, detail="No fue posible consultar la cobertura curricular local.") from error
