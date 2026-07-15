import json
import logging

from openai import OpenAIError
from pydantic import ValidationError

from app.agents.base import Agent, AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response
from app.curriculum.models import CurriculumEntry
from app.curriculum.provider import CurriculumProvider, JsonCurriculumProvider
from app.models.teaching_pack import CurriculumAlignment, CurriculumObjective, LessonPlan

logger = logging.getLogger(__name__)


class PlannerGenerationError(RuntimeError):
    """Raised after the planner exhausts its bounded structured-output retries."""


class PlannerAgent(Agent[LessonPlan]):
    """Maps a teacher request to verified OA objectives and a lesson structure."""

    max_attempts = 2

    def __init__(self, curriculum: CurriculumProvider | None = None) -> None:
        self.curriculum = curriculum or JsonCurriculumProvider()

    async def run(self, context: AgentContext) -> LessonPlan:
        candidates = self.curriculum.candidates(
            context.request.subject, context.request.grade_level
        )
        system_context = self._system_context(context.system_context, candidates)
        user_prompt = self._user_prompt(context, candidates)
        model = settings.planner_model or context.model or settings.openai_model

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                plan = await parse_structured_response(
                    model=model,
                    system_context=system_context,
                    user_prompt=user_prompt,
                    response_format=LessonPlan,
                )
                if plan is None:
                    raise ValueError("El modelo no devolvió una salida estructurada.")
                return self._verify_alignment(plan, candidates)
            except (OpenAIError, ValidationError, ValueError) as error:
                last_error = error
                logger.warning("Fallo del planificador, intento %s/%s: %s", attempt, self.max_attempts, error)

        raise PlannerGenerationError(
            "No fue posible generar un plan de clase válido. Intenta nuevamente."
        ) from last_error

    def _system_context(
        self, supplied_context: str, candidates: list[CurriculumEntry]
    ) -> str:
        # The stable shared text and complete provider data are both first, before
        # variable teacher input, to maximize exact-prefix prompt-cache reuse.
        shared = supplied_context or SHARED_SYSTEM_CONTEXT
        return f"""{shared}

REFERENCIA CURRICULAR ESTRUCTURADA (fuente autorizada para OA):
{self.curriculum.cache_context()}

INSTRUCCIONES DEL PLANIFICADOR:
- Responde exclusivamente en español para contenido dirigido a docentes.
- Usa solamente códigos y descripciones OA incluidos en la referencia curricular.
- Si no hay candidatos para asignatura/curso, usa status 'not_found', objectives [], y una nota clara. Nunca inventes códigos OA.
- Si existen candidatos pero ninguno corresponde al tema, usa status 'partial' u 'not_found' y explica la limitación.
- La suma de duration_minutes de stages debe ser igual a duration_minutes.
- El Planner define la estructura pedagógica: cada etapa contiene solamente nombre,
  duración, propósito y verificación formativa opcional. No incluyas instrucciones
  de docente, acciones de estudiantes ni coreografía de aula; eso corresponde al Designer.
"""

    def _user_prompt(
        self, context: AgentContext, candidates: list[CurriculumEntry]
    ) -> str:
        request = context.request.model_dump(exclude_none=True)
        candidate_json = json.dumps(
            [candidate.model_dump(mode="json") for candidate in candidates],
            ensure_ascii=False,
        )
        return f"""Planifica la siguiente clase para una docente.

SOLICITUD DOCENTE:
{json.dumps(request, ensure_ascii=False)}

CANDIDATOS RECUPERADOS PARA ESTA SOLICITUD:
{candidate_json}

Devuelve un LessonPlan completo. El título, conceptos, materiales, prerrequisitos,
objetivos y todas las etapas deben estar en español. No incluyas OA fuera de los
candidatos recuperados. Si la solicitud no especifica duración, propone una duración
razonable y distribúyela exactamente entre las etapas.
"""

    @staticmethod
    def _verify_alignment(
        plan: LessonPlan, candidates: list[CurriculumEntry]
    ) -> LessonPlan:
        approved = {
            entry.objective.code: entry.objective
            for entry in candidates
        }
        alignment = plan.curriculum_alignment

        if sum(stage.duration_minutes for stage in plan.stages) != plan.duration_minutes:
            raise ValueError("La duración de las etapas no coincide con la duración total.")

        if not approved:
            if alignment.objectives:
                raise ValueError("El modelo devolvió OA aunque no había datos curriculares candidatos.")
            return plan.model_copy(
                update={
                    "curriculum_alignment": CurriculumAlignment(
                        status="not_found",
                        objectives=[],
                        notes=alignment.notes or [
                            "No hay Objetivos de Aprendizaje disponibles para la asignatura o curso solicitado."
                        ],
                    )
                }
            )

        verified: list[CurriculumObjective] = []
        for objective in alignment.objectives:
            official = approved.get(objective.code)
            if official is None:
                raise ValueError(f"OA no presente en la fuente curricular: {objective.code}")
            # Canonicalize official text/source rather than trusting model copies.
            verified.append(official)

        if alignment.status == "aligned" and not verified:
            raise ValueError("Una alineación completa debe incluir al menos un OA verificado.")
        return plan.model_copy(
            update={
                "curriculum_alignment": alignment.model_copy(update={"objectives": verified})
            }
        )
