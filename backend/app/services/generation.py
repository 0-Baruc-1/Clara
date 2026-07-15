"""Orchestration for the validated Planner → Designer pipeline."""
import json
from collections.abc import AsyncIterator

from app.agents.base import AgentContext
from app.agents.designer import DesignerAgent, DesignerGenerationError
from app.agents.assessment import AssessmentAgent, AssessmentGenerationError
from app.agents.planner import PlannerAgent, PlannerGenerationError
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import LessonRequest


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
    except (PlannerGenerationError, DesignerGenerationError, AssessmentGenerationError) as error:
        yield sse_event("failure", {"message": str(error)})
    except RuntimeError as error:
        yield sse_event("failure", {"message": str(error)})
    except Exception:
        yield sse_event(
            "failure",
            {"message": "No fue posible preparar tu material. Por favor, inténtalo nuevamente."},
        )
