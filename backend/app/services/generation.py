from app.models.requests import LessonRequest
from app.models.teaching_pack import (
    ActivityGuide,
    ActivityDifferentiation,
    Assessment,
    CurriculumAlignment,
    ClassroomActivity,
    LessonPlan,
    LessonStage,
    RubricCriterion,
    TeachingPack,
)

async def generate_teaching_pack(request: LessonRequest) -> TeachingPack:
    """Temporary typed response until the agent orchestration is implemented."""
    # TODO: Build AgentContext; run Planner, Designer, Assessment, then Reviewer.
    # Shared system context must be the stable prefix of every model request.
    return TeachingPack(
        lesson_plan=LessonPlan(title="Plan de clase (borrador)", subject=request.subject or "Asignatura por definir", grade_level=request.grade_level or "Curso por definir", duration_minutes=request.duration_minutes or 90, curriculum_alignment=CurriculumAlignment(status="not_found", notes=["Respuesta de ejemplo: aún no se ha consultado el planificador."], objectives=[]), learning_objectives=["Objetivo curricular por definir con el agente planificador."], key_concepts=["Concepto por definir"], prerequisite_knowledge=["Conocimientos previos por definir"], materials=["Materiales por definir"], stages=[LessonStage(name="Inicio", duration_minutes=request.duration_minutes or 90, purpose="Recuperar conocimientos previos.", formative_check="Escuchar y registrar ideas previas.")]),
        activities=ActivityGuide(title="Actividad de aprendizaje (borrador)", overview="Actividad de ejemplo hasta conectar el agente diseñador.", targeted_learning_objectives=["Objetivo curricular por definir con el agente planificador."], activities=[ClassroomActivity(stage_name="Inicio", title="Activación de ideas previas", duration_minutes=request.duration_minutes or 90, grouping="curso completo", purpose="Recuperar conocimientos previos.", teacher_instructions=["Presentar una pregunta inicial.", "Registrar ideas del curso."], expected_student_output="Ideas previas compartidas oralmente.", materials=["Pizarra"], differentiation=ActivityDifferentiation(support="Ofrecer ejemplos visuales.", extension="Pedir que justifiquen sus ideas."))], materials_summary=["Pizarra"]),
        assessment=Assessment(title="Evaluación de salida (borrador)", instructions=["Explica con tus palabras el aprendizaje principal de la clase."], rubric=[RubricCriterion(criterion="Comprensión del objetivo", achieved="Explica el aprendizaje con precisión y un ejemplo.", developing="Explica parcialmente el aprendizaje.", beginning="Requiere apoyo para explicar el aprendizaje.")]),
        review_notes=["Respuesta de ejemplo: la revisión de consistencia se implementará próximamente."],
    )
