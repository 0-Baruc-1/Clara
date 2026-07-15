import json
from collections import defaultdict
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response
from app.models.teaching_pack import Assessment, AssessmentDraft, LessonPlan, SpecificationRow

class AssessmentGenerationError(RuntimeError): pass

class AssessmentAgent:
    max_attempts = 2
    async def run(self, context: AgentContext, plan: LessonPlan, activities: object | None = None) -> Assessment:
        prompt = f"""Diseña una evaluación final de la clase completa, no repitas las verificaciones formativas de etapas. Responde en español. Usa exclusivamente estos objetivos exactos: {json.dumps(plan.learning_objectives, ensure_ascii=False)}. Cubre cada objetivo con al menos un ítem. Para selección múltiple, correct_option_label debe ser exactamente la etiqueta de la alternativa correcta (por ejemplo, A); expected_answer debe explicar el criterio o razonamiento en prosa. Los ítems deben tener respuestas observables y una rúbrica concreta. El tiempo sugerido no puede exceder {plan.duration_minutes} minutos. No inventes OA ni tabla de especificaciones; el sistema la deriva.\nPLAN:\n{json.dumps(plan.model_dump(mode='json'), ensure_ascii=False)}"""
        error = None
        for attempt in range(self.max_attempts):
            try:
                draft = await parse_structured_response(model=settings.assessment_model or context.model or settings.openai_model, system_context=f"{context.system_context or SHARED_SYSTEM_CONTEXT}\nEres el agente de evaluación de Clara.", user_prompt=prompt, response_format=AssessmentDraft)
                if draft is None: raise ValueError("El modelo no devolvió una evaluación estructurada.")
                return self._validate(draft, plan)
            except (OpenAIError, ValidationError, ValueError) as exc:
                error = exc
                if attempt == 0:
                    prompt += f"\n\nCORRECCIÓN OBLIGATORIA DEL INTENTO ANTERIOR: {exc}. Corrige este problema exacto y devuelve una evaluación completa."
        raise AssessmentGenerationError("No fue posible generar una evaluación válida. Intenta nuevamente.") from error

    @staticmethod
    def _validate(draft: AssessmentDraft, plan: LessonPlan) -> Assessment:
        allowed = set(plan.learning_objectives); ids = {item.id for item in draft.items}
        if len(ids) != len(draft.items): raise ValueError("Ítems duplicados: cada id debe ser único.")
        if draft.suggested_application_minutes > plan.duration_minutes: raise ValueError("El tiempo de aplicación excede la duración de la clase.")
        if sum(item.points for item in draft.items) != draft.total_points: raise ValueError("Los puntajes no coinciden con el total declarado.")
        measured = {item.learning_objective for item in draft.items}
        if not measured <= allowed or measured != allowed: raise ValueError("La evaluación no mide exactamente todos los objetivos del plan.")
        for item in draft.items:
            if item.type == "selección múltiple":
                labels = {o.label for o in item.options}
                if len(item.options) < 2: raise ValueError(f"Ítem {item.id}: se esperaban al menos 2 alternativas; se recibieron {len(item.options)}.")
                if item.correct_option_label not in labels: raise ValueError(f"Ítem {item.id}: correct_option_label debe ser una de {sorted(labels)}; se recibió {item.correct_option_label!r}.")
            elif item.options or item.correct_option_label is not None: raise ValueError(f"Ítem {item.id}: solo selección múltiple puede incluir alternativas o correct_option_label.")
        rubric_ids = {item_id for criterion in draft.rubric for item_id in criterion.item_ids}
        if not rubric_ids <= ids or any(item.type != "selección múltiple" and item.id not in rubric_ids for item in draft.items): raise ValueError("La rúbrica no corresponde a los ítems abiertos.")
        grouped = defaultdict(list)
        for item in draft.items: grouped[item.learning_objective].append(item)
        table = [SpecificationRow(learning_objective=objective, item_count=len(items), item_ids=[item.id for item in items], total_points=sum(item.points for item in items), cognitive_levels=list(dict.fromkeys(item.cognitive_level for item in items))) for objective, items in grouped.items()]
        return Assessment(title=draft.title, instructions=draft.instructions, suggested_application_minutes=draft.suggested_application_minutes, total_points=draft.total_points, specification_table=table, items=draft.items, rubric=draft.rubric)
