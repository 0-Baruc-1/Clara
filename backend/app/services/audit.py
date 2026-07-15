from collections.abc import AsyncIterator
from app.agents.base import AgentContext
from app.agents.importer import ImporterAgent, ImportGenerationError
from app.agents.reviewer import ReviewerAgent, ReviewerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import AuditRequest, LessonRequest
from app.models.teaching_pack import AuditReport, ReviewFinding
from app.services.generation import sse_event, curriculum_tool_summary

ABSENCE_CATEGORIES = {"objective_coherence", "grounding"}

def conservative_findings(findings: list[ReviewFinding], activity_confidence: str, assessment_confidence: str) -> list[ReviewFinding]:
    """Presence facts remain; claims based on missing content need high-confidence parsing."""
    if activity_confidence == "alta" and assessment_confidence == "alta": return findings
    return [finding for finding in findings if finding.category not in ABSENCE_CATEGORIES or finding.category == "curriculum_honesty"]

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
