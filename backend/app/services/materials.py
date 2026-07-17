"""SSE orchestration for on-demand printable materials."""
import json
from collections.abc import AsyncIterator
from app.agents.base import AgentContext
from app.agents.materials import MaterialsAgent, MaterialsGenerationError
from app.agents.reviewer import ReviewerAgent, ReviewerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.fixtures.water_pack import water_materials, water_review
from app.models.requests import LessonRequest, MaterialsRequest
from app.models.teaching_pack import MaterialPack, ReviewCorrection, ReviewFinding
from app.services.generation import sse_event

def _coverage_findings(report, materials: MaterialPack):
    findings = list(report.findings)
    for coverage in materials.coverage:
        if coverage.fulfillment == "sin_cobertura" and not any(f.category == "coverage" and f.artifact_id == coverage.source_material_label for f in findings):
            findings.append(ReviewFinding(id=f"coverage-{coverage.activity_id}", severity="importante", responsible_agent="materials", category="coverage", artifact_type="material", artifact_id=coverage.source_material_label, description=f"La actividad {coverage.activity_id} solicita '{coverage.source_material_label}', pero no hay una hoja imprimible que la cubra.", suggested_correction="Genera o adapta esta hoja antes de usar la actividad."))
    return report.model_copy(update={"status": "findings_remaining" if findings else "clean", "findings": findings})

async def generate_materials_events(request: MaterialsRequest, *, api_key: str | None = None) -> AsyncIterator[str]:
    if settings.mock_mode:
        materials = water_materials()
        yield sse_event("materials_started", {"message": "El agente de Materiales está preparando hojas de ejemplo."})
        yield sse_event("materials_completed", {"materials": materials.model_dump(mode="json")})
        yield sse_event("materials_reviewer_started", {"message": "El Revisor está comprobando las hojas de ejemplo."})
        yield sse_event("materials_reviewer_correcting", {"message": "El Revisor revisó una corrección focalizada de los materiales."})
        report = water_review().model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent="materials", outcome="corrected")})
        yield sse_event("materials_reviewer_completed", {"materials": materials.model_dump(mode="json"), "review": report.model_dump(mode="json")})
        return
    context = AgentContext(request=LessonRequest(description="Generación bajo demanda de materiales."), system_context=SHARED_SYSTEM_CONTEXT, model=settings.openai_model, api_key=api_key)
    try:
        yield sse_event("materials_started", {"message": "El agente de Materiales está preparando hojas para el aula."})
        materials = await MaterialsAgent().run(context, request.activities)
        yield sse_event("materials_completed", {"materials": materials.model_dump(mode="json")})
        yield sse_event("materials_reviewer_started", {"message": "El Revisor está comprobando que cada hoja corresponda a la actividad."})
        report = _coverage_findings(await ReviewerAgent().run(context, request.lesson_plan, request.activities, request.assessment, materials), materials)
        blockers = [f for f in report.findings if f.severity == "bloqueante" and f.responsible_agent == "materials"]
        if blockers:
            yield sse_event("materials_reviewer_correcting", {"message": "El Revisor envió los materiales a una corrección focalizada."})
            try:
                notes = "\n\nCORRECCIÓN OBLIGATORIA DEL REVISOR:\n" + json.dumps([f.model_dump(mode="json") for f in blockers], ensure_ascii=False)
                materials = await MaterialsAgent().run(context, request.activities, notes)
                report = _coverage_findings(await ReviewerAgent().run(context, request.lesson_plan, request.activities, request.assessment, materials), materials)
                outcome = "corrected" if not any(f.severity == "bloqueante" for f in report.findings) else "findings_remaining"
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent="materials", outcome=outcome)})
            except Exception:
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent="materials", outcome="regeneration_failed")})
        yield sse_event("materials_reviewer_completed", {"materials": materials.model_dump(mode="json"), "review": report.model_dump(mode="json")})
    except (MaterialsGenerationError, ReviewerGenerationError) as error:
        yield sse_event("materials_failure", {"message": str(error)})
    except Exception:
        yield sse_event("materials_failure", {"message": "No fue posible preparar los materiales. Intenta nuevamente."})
