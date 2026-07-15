"""Run the Planner → Designer chain against Clara's bundled curriculum sample."""
import asyncio

from app.agents.base import AgentContext
from app.agents.designer import DesignerAgent
from app.agents.assessment import AssessmentAgent
from app.agents.planner import PlannerAgent
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import LessonRequest


def print_time_summary(plan, guide) -> None:
    """Show the per-stage coverage and time constraints checked by Designer."""
    activity_minutes = {
        stage.name: sum(
            activity.duration_minutes
            for activity in guide.activities
            if activity.stage_name == stage.name
        )
        for stage in plan.stages
    }

    print("\n=== Resumen de consistencia temporal ===")
    for stage in plan.stages:
        total = activity_minutes[stage.name]
        print(
            f"{stage.name}: presupuesto {stage.duration_minutes} min | "
            f"actividades {total} min | "
            f"{'OK' if 0 < total <= stage.duration_minutes else 'INVÁLIDO'}"
        )


async def main() -> None:
    request = LessonRequest(
        description=(
            "Clase práctica sobre cambios de estado del agua con una evaluación "
            "formativa de salida."
        ),
        subject="Ciencias Naturales",
        grade_level="6° básico",
        topic="Cambios de estado del agua",
        duration_minutes=90,
    )
    context = AgentContext(
        request=request,
        system_context=SHARED_SYSTEM_CONTEXT,
        model=settings.openai_model,
    )

    plan = await PlannerAgent().run(context)
    guide = await DesignerAgent().run(context, plan)
    assessment = await AssessmentAgent().run(context, plan, guide)

    print("=== LessonPlan ===")
    print(plan.model_dump_json(indent=2))
    print("\n=== ActivityGuide ===")
    print(guide.model_dump_json(indent=2))
    print("\n=== Assessment ===")
    print(assessment.model_dump_json(indent=2))
    print_time_summary(plan, guide)
    print("\n=== Cobertura y puntaje de evaluación ===")
    for row in assessment.specification_table:
        print(f"{row.learning_objective}: {', '.join(row.item_ids)} | {row.total_points} puntos")
    print(f"Puntaje: {sum(item.points for item in assessment.items)}/{assessment.total_points}")


if __name__ == "__main__":
    asyncio.run(main())
