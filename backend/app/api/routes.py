from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.requests import AuditRequest, EditedPackReviewRequest, LessonRequest, MaterialsRequest
from app.services.generation import generate_teaching_pack_events
from app.services.materials import generate_materials_events
from app.services.audit import audit_material_events, review_edited_pack_events
from app.services.coverage import coverage_overview
from app.core.config import settings
from app.models.coverage import CoverageOverview
from app.models.student_section import (
    PublishPracticeMaterialRequest,
    PublishPracticeMaterialResponse,
    StudentPracticeMaterial,
    StudentMaterialRelease,
    StudentObjectiveEvidence,
    StudentResponseReceipt,
    StudentResponseRequest,
)
from app.core.supabase_auth import authenticated_supabase_user
from app.curriculum.provider import JsonCurriculumProvider
from app.services.student_evidence import (
    DeterministicValidationError,
    deterministic_feedback,
    prepare_publication_for_attestation,
)
from app.services.supabase_student_store import StudentStoreUnavailable, SupabaseStudentStore

router = APIRouter()
student_store = SupabaseStudentStore()


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


@router.post("/student-materials/publish", response_model=PublishPracticeMaterialResponse)
async def publish_student_material(
    request: PublishPracticeMaterialRequest,
    user: tuple[UUID, str] = Depends(authenticated_supabase_user),
) -> PublishPracticeMaterialResponse:
    """Teacher approval creates an immutable, host-attested student snapshot."""
    teacher_id, access_token = user
    try:
        prepared_result = prepare_publication_for_attestation(request, JsonCurriculumProvider())
        publication_id, release_id = await student_store.publish(
            teacher_id=teacher_id, access_token=access_token, prepared=prepared_result.publication, class_id=request.class_id
        )
    except StudentStoreUnavailable as error:
        raise HTTPException(status_code=503, detail="No fue posible publicar el material para estudiantes.") from error
    except Exception as error:
        # Invalid OA labels are converted to practice-only items by design. Any
        # remaining failure is safe to show without exposing database internals.
        raise HTTPException(status_code=400, detail="No fue posible preparar esta publicación de forma segura.") from error
    practice_only = sum(item.evidence_objective_code is None for item in prepared_result.publication.items)
    return PublishPracticeMaterialResponse(
        publication_version_id=publication_id,
        release_id=release_id,
        published_item_count=len(prepared_result.publication.items),
        attested_objective_codes=[item.objective_code for item in prepared_result.publication.objectives],
        practice_only_item_count=practice_only,
        note=(
            "La profesora aprobó y atestiguó los OA verificados de esta publicación. "
            "Los ítems sin OA verificable se publicaron solo como práctica y no generarán evidencia curricular."
            if practice_only else
            "La profesora aprobó y atestiguó los OA verificados de esta publicación."
        ),
    )


@router.get("/student-materials/{release_id}", response_model=StudentPracticeMaterial)
async def student_material(
    release_id: str,
    user: tuple[UUID, str] = Depends(authenticated_supabase_user),
) -> StudentPracticeMaterial:
    """Read through the database RPC that recomputes both snapshot hashes."""
    _, access_token = user
    try:
        return await student_store.student_material(release_id=UUID(release_id), access_token=access_token)
    except (ValueError, StudentStoreUnavailable) as error:
        raise HTTPException(status_code=404, detail="Este material no está disponible o no superó su verificación de integridad.") from error


@router.get("/student-materials", response_model=list[StudentMaterialRelease])
async def student_materials(
    user: tuple[UUID, str] = Depends(authenticated_supabase_user),
) -> list[StudentMaterialRelease]:
    """Discover only releases permitted by the authenticated student's RLS policy."""
    user_id, access_token = user
    try:
        if await student_store.own_role(user_id=user_id, access_token=access_token) != "student":
            raise HTTPException(status_code=403, detail="Esta lista está disponible solo para estudiantes.")
        return await student_store.student_material_releases(access_token=access_token)
    except StudentStoreUnavailable as error:
        raise HTTPException(status_code=503, detail="No fue posible consultar tus materiales disponibles.") from error


@router.post("/student-items/{item_id}/responses", response_model=StudentResponseReceipt)
async def submit_student_response(
    item_id: str,
    request: StudentResponseRequest,
    user: tuple[UUID, str] = Depends(authenticated_supabase_user),
) -> StudentResponseReceipt:
    """Provide feedback only from a frozen, host-validated deterministic recipe."""
    _, access_token = user
    response_id = None
    try:
        parsed_item_id = UUID(item_id)
        response_id = await student_store.submit_response(item_id=parsed_item_id, answer=request.answer, access_token=access_token)
        mode, recipe = await student_store.item_validation(parsed_item_id)
        if mode != "deterministic":
            return StudentResponseReceipt(
                response_attempt_id=response_id,
                feedback_state="not_applicable",
                feedback_message="Tu respuesta fue enviada para que tu profesora la revise.",
            )
        if recipe is None:
            return StudentResponseReceipt(
                response_attempt_id=response_id,
                feedback_state="unavailable",
                feedback_message="Tu respuesta fue enviada. Esta pregunta requiere revisión de tu profesora.",
            )
        feedback = deterministic_feedback(recipe, request.answer)
        await student_store.attach_feedback(response_attempt_id=response_id, feedback=feedback)
        return StudentResponseReceipt(response_attempt_id=response_id, feedback_state="verified", feedback_message=feedback["message"])
    except DeterministicValidationError as error:
        # A malformed recipe or answer must never be translated into “incorrect”.
        if response_id is None:
            raise HTTPException(status_code=400, detail="No fue posible enviar tu respuesta de forma segura.") from error
        return StudentResponseReceipt(
            response_attempt_id=response_id,
            feedback_state="unavailable",
            feedback_message="Tu respuesta fue enviada. Esta pregunta requiere revisión de tu profesora.",
        )
    except (ValueError, StudentStoreUnavailable) as error:
        if response_id is not None:
            # Submission succeeded; a later infrastructure problem must not
            # invite the student to repeat it or imply a wrong answer.
            return StudentResponseReceipt(
                response_attempt_id=response_id,
                feedback_state="unavailable",
                feedback_message="Tu respuesta fue enviada. Esta pregunta requiere revisión de tu profesora.",
            )
        raise HTTPException(status_code=400, detail="No fue posible enviar tu respuesta de forma segura.") from error


@router.get("/classes/{class_id}/student-evidence", response_model=list[StudentObjectiveEvidence])
async def class_student_evidence(
    class_id: str,
    user: tuple[UUID, str] = Depends(authenticated_supabase_user),
) -> list[StudentObjectiveEvidence]:
    """Teacher-facing counts only; this endpoint never returns mastery labels."""
    _, access_token = user
    try:
        return await student_store.teacher_evidence(class_id=UUID(class_id), access_token=access_token)
    except (ValueError, StudentStoreUnavailable) as error:
        raise HTTPException(status_code=400, detail="No fue posible consultar la evidencia de respuestas del curso.") from error
