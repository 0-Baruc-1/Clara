"""Generate a plan against the bundled sample Chilean curriculum data."""
import asyncio

from app.agents.base import AgentContext
from app.agents.planner import PlannerAgent
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import LessonRequest


async def main() -> None:
    request = LessonRequest(
        description="Clase práctica sobre cambios de estado del agua con una evaluación formativa de salida.",
        subject="Ciencias Naturales",
        grade_level="6° básico",
        topic="Cambios de estado del agua",
        duration_minutes=90,
    )
    context = AgentContext(
        request=request,
        system_context=SHARED_SYSTEM_CONTEXT,
        model=settings.planner_model or settings.openai_model,
    )
    plan = await PlannerAgent().run(context)
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
