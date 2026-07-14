from app.models.requests import LessonRequest
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan, RubricCriterion, TeachingPack

async def generate_teaching_pack(request: LessonRequest) -> TeachingPack:
    """Temporary typed response until the agent orchestration is implemented."""
    # TODO: Build AgentContext; run Planner, Designer, Assessment, then Reviewer.
    # Shared system context must be the stable prefix of every model request.
    return TeachingPack(
        lesson_plan=LessonPlan(title="Plan de clase (borrador)", learning_objectives=["Objetivo curricular por definir con el agente planificador."], duration_minutes=90, sequence=["Inicio: recuperar conocimientos previos.", "Desarrollo: explorar el contenido mediante una actividad guiada.", "Cierre: sintetizar y verificar la comprensión."]),
        activities=ActivityGuide(title="Actividad de aprendizaje (borrador)", materials=["Materiales por definir."], instructions=["Formar grupos pequeños.", "Resolver el desafío relacionado con la clase.", "Compartir una conclusión con el curso."]),
        assessment=Assessment(title="Evaluación de salida (borrador)", instructions=["Explica con tus palabras el aprendizaje principal de la clase."], rubric=[RubricCriterion(criterion="Comprensión del objetivo", achieved="Explica el aprendizaje con precisión y un ejemplo.", developing="Explica parcialmente el aprendizaje.", beginning="Requiere apoyo para explicar el aprendizaje.")]),
        review_notes=["Respuesta de ejemplo: la revisión de consistencia se implementará próximamente."],
    )

