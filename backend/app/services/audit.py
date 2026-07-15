from collections.abc import AsyncIterator
from app.agents.base import AgentContext
from app.agents.importer import ImporterAgent, ImportGenerationError
from app.agents.reviewer import ReviewerAgent, ReviewerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import AuditRequest, EditedPackReviewRequest, LessonRequest
from app.models.teaching_pack import AuditReport, ReviewFinding
from app.services.generation import sse_event, curriculum_tool_summary

ABSENCE_CATEGORIES = {"objective_coherence", "grounding"}

def conservative_findings(findings: list[ReviewFinding], activity_confidence: str, assessment_confidence: str) -> list[ReviewFinding]:
    """Presence facts remain; claims based on missing content need high-confidence parsing."""
    if activity_confidence == "alta" and assessment_confidence == "alta": return findings
    return [finding for finding in findings if finding.category not in ABSENCE_CATEGORIES or finding.category == "curriculum_honesty"]


def frame_teacher_edit_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    """Keep coherence gaps as observations about the edited artifact, never a verdict on its author."""
    framed: list[ReviewFinding] = []
    for finding in findings:
        if finding.category in ABSENCE_CATEGORIES:
            finding = finding.model_copy(update={
                "description": (
                    "Al revisar la versión editada, Clara no encontró evidencia explícita en el material "
                    f"para confirmar esta relación ({finding.artifact_id}). Revisa la sugerencia antes de usarla en clase."
                )
            })
        framed.append(finding)
    return framed

async def audit_material_events(request: AuditRequest) -> AsyncIterator[str]:
    context = AgentContext(request=LessonRequest(description="Auditoría de material externo."), system_context=SHARED_SYSTEM_CONTEXT, model=settings.openai_model)
    try:
        yield sse_event("audit_parse_started", {"message": "Clara está identificando objetivos, actividades y evaluación."})
        bundle = await ImporterAgent().run(context, request.content, request.declared_kind)
        yield sse_event("audit_parse_completed", {"bundle": bundle.model_dump(mode="json")})
        if not bundle.lesson_plan or not bundle.activities or not bundle.assessment:
            report = AuditReport(overall_status="requiere_atencion", source_summary=bundle.source_summary, parse_confidence=bundle.parse_confidence, parse_notes=bundle.parse_notes, findings=[])
            yield sse_event("audit_completed", {"report": report.model_dump(mode="json")}); return
        yield sse_event("audit_reviewer_started", {"message": "El Revisor está verificando el material contra el currículum."})
        reviewer = ReviewerAgent(); review = await reviewer.run(context, bundle.lesson_plan, bundle.activities, bundle.assessment)
        for call in reviewer.tool_trace:
            yield sse_event("agent_tool_completed", {"agent":"reviewer", "tool":call["tool"], "summary":curriculum_tool_summary("reviewer", call)})
        findings = conservative_findings(review.findings, bundle.activity_confidence, bundle.assessment_confidence)
        report = AuditReport(overall_status="requiere_atencion" if findings or bundle.parse_notes else "listo_para_revisar", source_summary=bundle.source_summary, parse_confidence=bundle.parse_confidence, parse_notes=bundle.parse_notes, findings=findings)
        yield sse_event("audit_completed", {"report": report.model_dump(mode="json")})
    except (ImportGenerationError, ReviewerGenerationError) as error:
        yield sse_event("audit_failure", {"message": str(error)})


async def review_edited_pack_events(request: EditedPackReviewRequest) -> AsyncIterator[str]:
    """Audit teacher changes without a parser pass; the structured fields are fully readable."""
    context = AgentContext(
        request=LessonRequest(description="Revisión de cambios realizados por una docente."),
        system_context=SHARED_SYSTEM_CONTEXT,
        model=settings.openai_model,
    )
    try:
        yield sse_event("edited_review_started", {"message": "Clara está revisando tus cambios contra el plan y el currículum."})
        reviewer = ReviewerAgent()
        review = await reviewer.run(
            context,
            request.lesson_plan,
            request.activities,
            request.assessment,
            request.materials,
            teacher_edit_mode=True,
        )
        for call in reviewer.tool_trace:
            yield sse_event("agent_tool_completed", {"agent": "reviewer", "tool": call["tool"], "summary": curriculum_tool_summary("reviewer", call)})
        findings = frame_teacher_edit_findings(conservative_findings(review.findings, "alta", "alta"))
        review = review.model_copy(update={
            "status": "findings_remaining" if findings else "clean",
            "findings": findings,
            "summary": "Revisión de la versión editada: " + review.summary,
        })
        yield sse_event("edited_review_completed", {"review": review.model_dump(mode="json")})
    except ReviewerGenerationError as error:
        yield sse_event("edited_review_failure", {"message": str(error)})
    except Exception:
        yield sse_event("edited_review_failure", {"message": "No fue posible revisar los cambios. Inténtalo nuevamente."})
