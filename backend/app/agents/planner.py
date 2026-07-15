import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import Agent, AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response_with_tools
from app.curriculum.provider import CurriculumProvider, JsonCurriculumProvider
from app.curriculum.tools import CURRICULUM_TOOLS, CurriculumToolFailure, curriculum_tool_handler
from app.models.teaching_pack import CurriculumAlignment, CurriculumObjective, LessonPlan

class PlannerGenerationError(RuntimeError): pass

class PlannerAgent(Agent[LessonPlan]):
    max_attempts = 2
    def __init__(self, curriculum: CurriculumProvider | None = None) -> None: self.curriculum = curriculum or JsonCurriculumProvider(); self.tool_trace: list[dict] = []
    async def run(self, context: AgentContext) -> LessonPlan:
        trace: list[dict] = []; self.tool_trace = trace; handler = curriculum_tool_handler(self.curriculum, trace)
        prompt = f"""Planifica esta clase en español: {json.dumps(context.request.model_dump(exclude_none=True), ensure_ascii=False)}. Debes llamar buscar_objetivos antes de responder. Si citas un OA, debes llamar verificar_objetivo para cada código. Si la búsqueda no encuentra cobertura, usa curriculum_alignment.status='not_found' y objectives=[]; nunca inventes OA. El Planner define estructura, no coreografía. La suma de etapas debe igualar la duración."""
        error = None
        for attempt in range(self.max_attempts):
            try:
                plan = await parse_structured_response_with_tools(model=settings.planner_model or context.model or settings.openai_model, system_context=f"{context.system_context or SHARED_SYSTEM_CONTEXT}\nHerramientas curriculares disponibles: busca y verifica desde la fuente, no desde memoria.", user_prompt=prompt, response_format=LessonPlan, tools=CURRICULUM_TOOLS, tool_handler=handler)
                return self._verify(plan, trace)
            except (OpenAIError, ValidationError, ValueError, CurriculumToolFailure, RuntimeError) as exc:
                error = exc; prompt += f"\nCORRECCIÓN OBLIGATORIA: {exc}."
        raise PlannerGenerationError("No fue posible consultar y verificar el currículum. Intenta nuevamente.") from error
    @staticmethod
    def _verify(plan: LessonPlan, trace: list[dict]) -> LessonPlan:
        if not any(item["tool"] == "buscar_objetivos" for item in trace): raise ValueError("El Planner no consultó la base curricular.")
        if sum(stage.duration_minutes for stage in plan.stages) != plan.duration_minutes: raise ValueError("La duración de las etapas no coincide con la duración total.")
        verified = {item["arguments"]["codigo"].casefold(): item["result"] for item in trace if item["tool"] == "verificar_objetivo"}
        objectives: list[CurriculumObjective] = []
        for objective in plan.curriculum_alignment.objectives:
            result = verified.get(objective.code.casefold())
            if not result or not result["existe"]: raise ValueError(f"OA sin verificación en esta ejecución: {objective.code}")
            official = result["objetivo"]["objective"] if "objective" in result["objetivo"] else result["objetivo"]
            objectives.append(CurriculumObjective(code=official["code"], description=official["description"], source=official.get("source", "Fuente curricular")))
        if not objectives:
            return plan.model_copy(update={"curriculum_alignment": CurriculumAlignment(status="not_found", objectives=[], notes=plan.curriculum_alignment.notes or ["No se encontraron OA verificados para la solicitud."])})
        return plan.model_copy(update={"curriculum_alignment": plan.curriculum_alignment.model_copy(update={"objectives": objectives})})
