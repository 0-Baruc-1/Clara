import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import parse_structured_response_with_tools
from app.curriculum.provider import JsonCurriculumProvider
from app.curriculum.tools import CURRICULUM_TOOLS, curriculum_tool_handler
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan, MaterialPack, ReviewCorrection, ReviewReport, ReviewReportDraft

class ReviewerGenerationError(RuntimeError): pass

class ReviewerAgent:
    def __init__(self) -> None: self.tool_trace: list[dict] = []
    async def run(self, context: AgentContext, plan: LessonPlan, activities: ActivityGuide, assessment: Assessment, materials: MaterialPack | None = None) -> ReviewReport:
        materials_context = "" if materials is None else f"""\nMATERIALES={json.dumps(materials.model_dump(mode='json'), ensure_ascii=False)}
También audita que cada hoja pertenezca a la actividad que la solicita; que tarjetas usen sólo conceptos enseñados; que tablas y organizadores recojan el producto esperado; y que tickets correspondan a la verificación formativa. Toda cobertura con fulfillment='sin_cobertura' debe ser un hallazgo category='coverage', responsible_agent='materials', no bloqueante."""
        codes = sorted({objective.code for objective in plan.curriculum_alignment.objectives})
        trace: list[dict] = []; self.tool_trace = trace
        prompt = f"""Audita en español coherencia cruzada. Antes de responder debes llamar verificar_objetivo una vez por cada código en {codes}; no apruebes códigos sin verificar. Una pregunta puede aplicar un concepto a una situación cotidiana NUEVA, pero no puede afirmar que la clase observó, midió, registró, experimentó, usó una estación o tuvo evidencia de esa situación si no existe explícitamente en ACTIVIDADES. Trata evidencia inexistente como bloqueante de grounding y atribúyelo a assessment. Revisa también que suggested_application_minutes no exceda el tiempo de etapas de evaluación/evidencia del PLAN. No reescribas contenido. Devuelve hallazgos precisos con responsable, id y corrección.
PLAN={json.dumps(plan.model_dump(mode='json'), ensure_ascii=False)}
ACTIVIDADES={json.dumps(activities.model_dump(mode='json'), ensure_ascii=False)}
EVALUACION={json.dumps(assessment.model_dump(mode='json'), ensure_ascii=False)}{materials_context}"""
        try:
            out = await parse_structured_response_with_tools(model=settings.reviewer_model or context.model or settings.openai_model, system_context=f"{context.system_context}\nVerifica OA con herramientas curriculares; no uses memoria.", user_prompt=prompt, response_format=ReviewReportDraft, tools=CURRICULUM_TOOLS, tool_handler=curriculum_tool_handler(JsonCurriculumProvider(), trace))
            checked = {item["arguments"]["codigo"].casefold(): item["result"] for item in trace if item["tool"] == "verificar_objetivo"}
            missing = [code for code in codes if code.casefold() not in checked]
            invalid = [code for code in codes if code.casefold() in checked and not checked[code.casefold()]["existe"]]
            if missing: raise ValueError("El Revisor no verificó todos los OA: " + ", ".join(missing))
            if invalid:
                from app.models.teaching_pack import ReviewFinding
                out = out.model_copy(update={"status":"findings_remaining", "findings": out.findings + [ReviewFinding(id=f"oa-{code}", severity="bloqueante", responsible_agent="planner", category="curriculum_honesty", artifact_type="plan", artifact_id=code, description=f"El código {code} no existe en la fuente curricular.", suggested_correction="Elimina o reemplaza el OA por uno verificado.") for code in invalid]})
            return ReviewReport(status=out.status, summary=out.summary, findings=out.findings, correction=ReviewCorrection())
        except (OpenAIError, ValidationError, ValueError) as error:
            raise ReviewerGenerationError("No fue posible revisar la coherencia del pack.") from error
