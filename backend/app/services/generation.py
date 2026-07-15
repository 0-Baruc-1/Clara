"""SSE orchestration for the main reviewed teaching-pack flow."""
import json
from collections.abc import AsyncIterator
from app.agents.assessment import AssessmentAgent, AssessmentGenerationError
from app.agents.base import AgentContext
from app.agents.designer import DesignerAgent, DesignerGenerationError
from app.agents.planner import PlannerAgent, PlannerGenerationError
from app.agents.reviewer import ReviewerAgent, ReviewerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.fixtures.water_pack import water_assessment, water_guide, water_plan, water_review
from app.models.requests import LessonRequest
from app.models.teaching_pack import ReviewCorrection
from app.services.coverage import record_reviewed_pack

def sse_event(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def curriculum_tool_summary(agent: str, call: dict[str, object]) -> str:
    """Build readable, Python 3.11-safe summaries of curriculum tool use."""
    tool = str(call["tool"])
    arguments = call.get("arguments", {})
    if tool == "buscar_objetivos":
        result = call.get("result", {})
        count = len(result.get("objetivos", [])) if isinstance(result, dict) else 0
        return f"Planificador consultó la base curricular · {count} OA encontrados"
    code = arguments.get("codigo", "currículum") if isinstance(arguments, dict) else "currículum"
    label = "Revisor" if agent == "reviewer" else "Planificador"
    return f"{label} verificó {code}"

async def generate_teaching_pack_events(request: LessonRequest) -> AsyncIterator[str]:
    if settings.mock_mode:
        plan, guide, assessment, report = water_plan(), water_guide(), water_assessment(), water_review()
        yield sse_event("planner_started", {"message": "El Planificador está consultando la muestra curricular local."})
        yield sse_event("agent_tool_completed", {"agent": "planner", "tool": "buscar_objetivos", "summary": "Planificador consultó la base curricular de muestra · 2 OA encontrados"})
        yield sse_event("planner_completed", {"plan": plan.model_dump(mode="json")})
        yield sse_event("designer_started", {"message": "El Diseñador está preparando las actividades de ejemplo."})
        yield sse_event("designer_completed", {"activities": guide.model_dump(mode="json")})
        yield sse_event("assessment_started", {"message": "El Evaluador está preparando la evaluación de ejemplo."})
        yield sse_event("assessment_completed", {"assessment": assessment.model_dump(mode="json")})
        yield sse_event("reviewer_started", {"message": "El Revisor está comprobando la coherencia del ejemplo."})
        yield sse_event("reviewer_correcting", {"target_agent": "assessment", "message": "El Revisor revisó una corrección focalizada del Evaluador."})
        yield sse_event("reviewer_completed", {"review": report.model_dump(mode="json"), "activities": guide.model_dump(mode="json"), "assessment": assessment.model_dump(mode="json")})
        return
    context = AgentContext(request=request, system_context=SHARED_SYSTEM_CONTEXT, model=settings.openai_model)
    try:
        yield sse_event("planner_started", {"message": "El Planificador está vinculando la clase con el currículum."})
        planner = PlannerAgent(); plan = await planner.run(context)
        for call in getattr(planner, "tool_trace", []):
            yield sse_event("agent_tool_completed", {"agent": "planner", "tool": call["tool"], "summary": curriculum_tool_summary("planner", call)})
        yield sse_event("planner_completed", {"plan": plan.model_dump(mode="json")})
        yield sse_event("designer_started", {"message": "El Diseñador está convirtiendo el plan en experiencias de aula."})
        guide = await DesignerAgent().run(context, plan)
        yield sse_event("designer_completed", {"activities": guide.model_dump(mode="json")})
        yield sse_event("assessment_started", {"message": "El Evaluador está preparando el instrumento y la rúbrica."})
        assessment = await AssessmentAgent().run(context, plan, guide)
        yield sse_event("assessment_completed", {"assessment": assessment.model_dump(mode="json")})
        yield sse_event("reviewer_started", {"message": "El Revisor está comprobando la coherencia entre plan, actividades y evaluación."})
        reviewer = ReviewerAgent(); report = await reviewer.run(context, plan, guide, assessment)
        for call in getattr(reviewer, "tool_trace", []):
            yield sse_event("agent_tool_completed", {"agent": "reviewer", "tool": call["tool"], "summary": curriculum_tool_summary("reviewer", call)})
        blockers = [finding for finding in report.findings if finding.severity == "bloqueante"]
        targets = [finding.responsible_agent for finding in blockers]
        target = "designer" if "designer" in targets else "assessment" if "assessment" in targets else None
        if target:
            yield sse_event("reviewer_correcting", {"target_agent": target, "message": f"El Revisor solicitó una corrección focalizada al {target}."})
            try:
                notes = "\n\nCORRECCIÓN OBLIGATORIA DEL REVISOR:\n" + json.dumps([finding.model_dump(mode="json") for finding in blockers if finding.responsible_agent == target], ensure_ascii=False)
                if target == "designer": guide = await DesignerAgent().run(context, plan, notes)
                else: assessment = await AssessmentAgent().run(context, plan, guide, notes)
                corrected_reviewer = ReviewerAgent()
                report = await corrected_reviewer.run(context, plan, guide, assessment)
                reviewer = corrected_reviewer
                for call in getattr(reviewer, "tool_trace", []):
                    yield sse_event("agent_tool_completed", {"agent": "reviewer", "tool": call["tool"], "summary": curriculum_tool_summary("reviewer", call)})
                outcome = "corrected" if not any(finding.severity == "bloqueante" for finding in report.findings) else "findings_remaining"
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent=target, outcome=outcome)})
            except Exception:
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent=target, outcome="regeneration_failed")})
        elif "planner" in targets:
            report = report.model_copy(update={"summary": report.summary + " Los hallazgos del Planner se muestran sin regeneración, porque cambiar el plan invalidaría los artefactos posteriores."})
        try:
            record_reviewed_pack(database_path=settings.coverage_db_path, session_id=request.teacher_session_id, source_type="generated", plan=plan, activities=guide, review=report, verification_trace=getattr(reviewer, "tool_trace", []))
        except Exception:
            # Coverage memory is helpful but must never prevent a teacher receiving their pack.
            pass
        yield sse_event("reviewer_completed", {"review": report.model_dump(mode="json"), "activities": guide.model_dump(mode="json"), "assessment": assessment.model_dump(mode="json")})
    except (PlannerGenerationError, DesignerGenerationError, AssessmentGenerationError, ReviewerGenerationError) as error:
        yield sse_event("failure", {"message": str(error)})
    except RuntimeError as error:
        yield sse_event("failure", {"message": str(error)})
    except Exception:
        yield sse_event("failure", {"message": "No fue posible preparar tu material. Por favor, inténtalo nuevamente."})
