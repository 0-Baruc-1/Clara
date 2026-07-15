"""Orchestration for the validated Planner → Designer pipeline."""
import json
from collections.abc import AsyncIterator

from app.agents.base import AgentContext
from app.agents.designer import DesignerAgent, DesignerGenerationError
from app.agents.assessment import AssessmentAgent, AssessmentGenerationError
from app.agents.reviewer import ReviewerAgent, ReviewerGenerationError
from app.agents.planner import PlannerAgent, PlannerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import LessonRequest
from app.models.teaching_pack import ReviewCorrection


def sse_event(event: str, data: dict[str, object]) -> str:
    """Serialize one SSE frame; JSON stays on one data line."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def generate_teaching_pack_events(request: LessonRequest) -> AsyncIterator[str]:
    """Yield milestones only after each agent has returned validated output."""
    context = AgentContext(
        request=request,
        system_context=SHARED_SYSTEM_CONTEXT,
        model=settings.openai_model,
    )
    try:
        yield sse_event(
            "planner_started",
            {"message": "El Planificador está vinculando la clase con el currículum."},
        )
        plan = await PlannerAgent().run(context)
        yield sse_event("planner_completed", {"plan": plan.model_dump(mode="json")})

        yield sse_event(
            "designer_started",
            {"message": "El Diseñador está convirtiendo el plan en experiencias de aula."},
        )
        guide = await DesignerAgent().run(context, plan)
        yield sse_event("designer_completed", {"activities": guide.model_dump(mode="json")})
        yield sse_event("assessment_started", {"message": "El Evaluador está preparando el instrumento y la rúbrica."})
        assessment = await AssessmentAgent().run(context, plan, guide)
        yield sse_event("assessment_completed", {"assessment": assessment.model_dump(mode="json")})
        yield sse_event("reviewer_started", {"message": "El Revisor está comprobando la coherencia entre plan, actividades y evaluación."})
        report = await ReviewerAgent().run(context, plan, guide, assessment)
        blockers = [f for f in report.findings if f.severity == "bloqueante"]
        targets = [f.responsible_agent for f in blockers]
        target = "designer" if "designer" in targets else "assessment" if "assessment" in targets else None
        if target:
            yield sse_event("reviewer_correcting", {"target_agent": target, "message": f"El Revisor solicitó una corrección focalizada al {target}."})
            # One bounded repair pass; planner blockers are intentionally surfaced only.
            try:
                notes = "\n\nCORRECCIÓN OBLIGATORIA DEL REVISOR: conserva lo correcto y corrige solamente estos hallazgos:\n" + json.dumps([f.model_dump(mode="json") for f in blockers if f.responsible_agent == target], ensure_ascii=False)
                if target == "designer": guide = await DesignerAgent().run(context, plan, notes)
                else: assessment = await AssessmentAgent().run(context, plan, guide, notes)
                report = await ReviewerAgent().run(context, plan, guide, assessment)
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent=target, outcome="corrected" if not any(f.severity == "bloqueante" for f in report.findings) else "findings_remaining")})
            except Exception:
                report = report.model_copy(update={"correction": ReviewCorrection(attempted=True, target_agent=target, outcome="regeneration_failed")})
        elif "planner" in targets:
            report = report.model_copy(update={"summary": report.summary + " Los hallazgos del Planner se muestran sin regeneración, porque cambiar el plan invalidaría los artefactos posteriores."})
        yield sse_event("reviewer_completed", {"review": report.model_dump(mode="json"), "activities": guide.model_dump(mode="json"), "assessment": assessment.model_dump(mode="json")})
    except (PlannerGenerationError, DesignerGenerationError, AssessmentGenerationError, ReviewerGenerationError) as error:
        yield sse_event("failure", {"message": str(error)})
    except RuntimeError as error:
        yield sse_event("failure", {"message": str(error)})
    except Exception:
        yield sse_event(
            "failure",
            {"message": "No fue posible preparar tu material. Por favor, inténtalo nuevamente."},
        )
