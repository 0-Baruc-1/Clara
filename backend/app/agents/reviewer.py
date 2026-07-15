import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import parse_structured_response
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan, ReviewCorrection, ReviewReport, ReviewReportDraft
class ReviewerGenerationError(RuntimeError): pass
class ReviewerAgent:
 async def run(self, context: AgentContext, plan: LessonPlan, activities: ActivityGuide, assessment: Assessment) -> ReviewReport:
  prompt=f"""Audita en español coherencia cruzada. La regla crítica de grounding: una pregunta puede aplicar un concepto a una situación cotidiana NUEVA (por ejemplo, ropa secándose), pero no puede afirmar que la clase observó, midió, registró, experimentó, usó una estación o tuvo evidencia de esa situación si no existe explícitamente en ACTIVIDADES. Trata referencias como 'estación final', 'medición realizada', 'experimento observado' o evidencia inexistente como bloqueante de grounding y atribúyelo a assessment_item. Revisa también que suggested_application_minutes no exceda el tiempo de etapas de evaluación/evidencia del PLAN; si no hay etapa explícita, indícalo como importante. No reescribas contenido. Devuelve hallazgos precisos con responsable, id y corrección. PLAN={json.dumps(plan.model_dump(mode='json'),ensure_ascii=False)} ACTIVIDADES={json.dumps(activities.model_dump(mode='json'),ensure_ascii=False)} EVALUACION={json.dumps(assessment.model_dump(mode='json'),ensure_ascii=False)}"""
  try:
   out=await parse_structured_response(model=settings.reviewer_model or context.model or settings.openai_model,system_context=context.system_context,user_prompt=prompt,response_format=ReviewReportDraft)
   if out is None: raise ValueError("Sin informe")
   return ReviewReport(status=out.status,summary=out.summary,findings=out.findings,correction=ReviewCorrection())
  except (OpenAIError,ValidationError,ValueError) as e: raise ReviewerGenerationError("No fue posible revisar la coherencia del pack.") from e
