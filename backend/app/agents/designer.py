import json
import logging

from openai import OpenAIError
from pydantic import ValidationError

from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response
from app.models.teaching_pack import ActivityGuide, ActivityGuideDraft, LessonPlan

logger = logging.getLogger(__name__)


class DesignerGenerationError(RuntimeError):
    """Raised when the Designer cannot return a valid guide after retrying."""


class DesignerAgent:
    """Creates timed, differentiated activities from an approved lesson plan."""

    max_attempts = 2

    async def run(self, context: AgentContext, plan: LessonPlan, repair_notes: str = "") -> ActivityGuide:
        self._validate_plan(plan)
        model = settings.designer_model or context.model or settings.openai_model
        system_context = self._system_context(context.system_context)
        user_prompt = self._user_prompt(plan) + repair_notes

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                draft = await parse_structured_response(
                    model=model,
                    system_context=system_context,
                    user_prompt=user_prompt,
                    response_format=ActivityGuideDraft,
                    api_key=context.api_key,
                )
                if draft is None:
                    raise ValueError("El modelo no devolvió una guía de actividades estructurada.")
                return self._verify_and_finalize(draft, plan)
            except (OpenAIError, ValidationError, ValueError) as error:
                last_error = error
                logger.warning("Fallo del diseñador, intento %s/%s", attempt, self.max_attempts)

        raise DesignerGenerationError(
            "No fue posible generar una guía de actividades válida. Intenta nuevamente."
        ) from last_error

    @staticmethod
    def _validate_plan(plan: LessonPlan) -> None:
        stage_names = [stage.name for stage in plan.stages]
        if len(stage_names) != len(set(stage_names)):
            raise DesignerGenerationError(
                "El plan de clase contiene etapas con nombres duplicados y no puede usarse para diseñar actividades."
            )

    @staticmethod
    def _system_context(supplied_context: str) -> str:
        shared = supplied_context or SHARED_SYSTEM_CONTEXT
        return f"""{shared}

INSTRUCCIONES DEL DISEÑADOR:
- Responde exclusivamente en español para contenido dirigido a docentes.
- Diseña actividades concretas, inclusivas y apropiadas para el nivel del plan.
- Usa solo objetivos de aprendizaje ya incluidos en el plan recibido; no inventes OA ni objetivos nuevos.
- Cada actividad debe indicar una etapa existente del plan y no puede exceder su tiempo disponible.
- Diseña la coreografía completa del aula: pasos de la docente, producto esperado,
  agrupamiento y diferenciación. Decide si cada etapa requiere una o varias actividades
  según su propósito y duración; no copies automáticamente una actividad por etapa.
- Cada etapa del plan debe tener al menos una actividad.
- Entrega instrucciones numeradas o secuenciales que una docente pueda ejecutar.
- Incluye una adaptación de apoyo y una extensión para cada actividad.
- No generes materials_summary: el sistema lo deriva desde los materiales de las actividades.
"""

    @staticmethod
    def _user_prompt(plan: LessonPlan) -> str:
        return f"""Crea una guía de actividades coherente con este LessonPlan validado:

{json.dumps(plan.model_dump(mode="json"), ensure_ascii=False)}

Los valores de targeted_learning_objectives deben copiarse exactamente desde
learning_objectives del plan. Los valores de stage_name deben copiarse exactamente
desde stages[].name. Todas las etapas del plan deben aparecer al menos una vez.
La suma de duraciones de actividades en cada etapa no puede superar los minutos
de esa etapa. Usa una o varias actividades por etapa según lo requiera el diseño,
sin reflejar las etapas mecánicamente. Devuelve una guía completa, pero omite
materials_summary porque el sistema la calculará.
"""

    @staticmethod
    def _verify_and_finalize(draft: ActivityGuideDraft, plan: LessonPlan) -> ActivityGuide:
        stage_budget = {stage.name: stage.duration_minutes for stage in plan.stages}
        allowed_objectives = set(plan.learning_objectives)

        unknown_objectives = set(draft.targeted_learning_objectives) - allowed_objectives
        if unknown_objectives:
            raise ValueError(
                "La guía incluyó objetivos que no pertenecen al plan: "
                + ", ".join(sorted(unknown_objectives))
            )

        time_by_stage: dict[str, int] = {}
        materials: list[str] = []
        seen_materials: set[str] = set()
        for activity in draft.activities:
            if activity.stage_name not in stage_budget:
                raise ValueError(f"La actividad referencia una etapa inexistente: {activity.stage_name}")
            time_by_stage[activity.stage_name] = (
                time_by_stage.get(activity.stage_name, 0) + activity.duration_minutes
            )
            for material in activity.materials:
                normalized = material.strip()
                if normalized and normalized.casefold() not in seen_materials:
                    seen_materials.add(normalized.casefold())
                    materials.append(normalized)

        for stage_name, total_duration in time_by_stage.items():
            if total_duration > stage_budget[stage_name]:
                raise ValueError(
                    f"Las actividades de '{stage_name}' usan {total_duration} minutos, "
                    f"pero la etapa tiene {stage_budget[stage_name]}."
                )

        missing_stages = set(stage_budget) - set(time_by_stage)
        if missing_stages:
            raise ValueError(
                "La guía no incluye actividades para las etapas: "
                + ", ".join(sorted(missing_stages))
            )

        return ActivityGuide(
            title=draft.title,
            overview=draft.overview,
            targeted_learning_objectives=draft.targeted_learning_objectives,
            activities=draft.activities,
            materials_summary=materials,
        )
