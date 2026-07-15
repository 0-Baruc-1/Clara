"""A realistic water lesson for offline demos; it never invokes an agent or API."""
from app.models.teaching_pack import (
    ActivityDifferentiation,
    ActivityGuide,
    Assessment,
    AssessmentItem,
    AssessmentOption,
    AuditReport,
    CurriculumAlignment,
    CurriculumObjective,
    LessonPlan,
    LessonStage,
    MaterialCoverage,
    MaterialPack,
    PrintableBlock,
    PrintableMaterial,
    ReviewCorrection,
    ReviewFinding,
    ReviewReport,
    RubricCriterion,
    RubricLevels,
    SpecificationRow,
)


OBJECTIVE_ONE = "Explicar los cambios de estado del agua a partir de observaciones de experiencias simples."
OBJECTIVE_TWO = "Relacionar temperatura y transferencia de calor con fusión, evaporación y condensación."


def water_plan() -> LessonPlan:
    return LessonPlan(
        title="Cambios de estado del agua",
        subject="Ciencias Naturales",
        grade_level="6° básico",
        duration_minutes=90,
        curriculum_alignment=CurriculumAlignment(
            status="aligned",
            notes=["OA consultados en la muestra curricular local de Clara."],
            objectives=[
                CurriculumObjective(
                    code="CN06 OA 13",
                    description="Demostrar, mediante la investigación experimental, los cambios de estado de la materia.",
                    source="Bases Curriculares Chile (muestra local)",
                ),
                CurriculumObjective(
                    code="CN06 OA 15",
                    description="Medir y registrar datos para responder preguntas científicas sencillas.",
                    source="Bases Curriculares Chile (muestra local)",
                ),
            ],
        ),
        learning_objectives=[OBJECTIVE_ONE, OBJECTIVE_TWO],
        key_concepts=["fusión", "evaporación", "condensación", "temperatura"],
        prerequisite_knowledge=["Estados sólido, líquido y gaseoso."],
        materials=["cubos de hielo", "vasos transparentes", "agua tibia", "film plástico", "hoja de registro"],
        stages=[
            LessonStage(name="Inicio", duration_minutes=15, purpose="Activar ideas previas sobre los estados del agua.", formative_check="Explicación oral de un cambio cotidiano."),
            LessonStage(name="Exploración", duration_minutes=50, purpose="Observar y registrar cambios de estado en experiencias seguras.", formative_check="Registro con evidencia y vocabulario científico."),
            LessonStage(name="Síntesis", duration_minutes=15, purpose="Relacionar los cambios observados con transferencia de calor.", formative_check="Mapa de cambios de estado."),
            LessonStage(name="Cierre y evaluación", duration_minutes=10, purpose="Comprobar la explicación individual de los cambios observados.", formative_check="Ticket de salida."),
        ],
    )


def water_guide() -> ActivityGuide:
    return ActivityGuide(
        title="Guía de actividades: cambios de estado del agua",
        overview="Experiencias breves, seguras y observables para explicar los cambios de estado.",
        targeted_learning_objectives=[OBJECTIVE_ONE, OBJECTIVE_TWO],
        activities=[
            {
                "id": "activity-1", "stage_name": "Inicio", "title": "¿Qué le pasa al hielo?", "duration_minutes": 15,
                "grouping": "curso completo", "purpose": "Recuperar explicaciones previas.",
                "teacher_instructions": ["Muestra un cubo de hielo en un vaso.", "Recoge hipótesis sobre lo que ocurrirá."],
                "expected_student_output": "Hipótesis oral sobre el cambio de estado.", "materials": ["cubo de hielo", "vaso"],
                "differentiation": ActivityDifferentiation(support="Ofrece imágenes de los estados.", extension="Pide explicar el papel del calor."),
            },
            {
                "id": "activity-2", "stage_name": "Exploración", "title": "Registro de fusión y condensación", "duration_minutes": 35,
                "grouping": "grupos", "purpose": "Observar evidencia y registrarla.",
                "teacher_instructions": ["Entregue hielo y un vaso con agua tibia cubierto con film.", "Pida registrar cambios y gotas observadas."],
                "expected_student_output": "Tabla con observaciones de fusión y condensación.", "materials": ["hielo", "agua tibia", "film plástico", "hoja de registro"],
                "differentiation": ActivityDifferentiation(support="Use una tabla con columnas ya nombradas.", extension="Pida distinguir observación de explicación."),
            },
            {
                "id": "activity-3", "stage_name": "Exploración", "title": "Tarjetas de vocabulario", "duration_minutes": 15,
                "grouping": "parejas", "purpose": "Nombrar los cambios observados con precisión.",
                "teacher_instructions": ["Distribuya tarjetas de conceptos.", "Pida asociar cada concepto con una evidencia del registro."],
                "expected_student_output": "Parejas concepto-evidencia justificadas.", "materials": ["tarjetas de vocabulario", "registro de observación"],
                "differentiation": ActivityDifferentiation(support="Entregue definiciones breves.", extension="Pida crear una tarjeta adicional."),
            },
            {
                "id": "activity-4", "stage_name": "Síntesis", "title": "Mapa de los cambios", "duration_minutes": 15,
                "grouping": "parejas", "purpose": "Relacionar estados y transferencia de calor.",
                "teacher_instructions": ["Modele una flecha entre sólido y líquido.", "Pida completar el organizador con flechas y palabras."],
                "expected_student_output": "Mapa de cambios de estado con flechas y referencias al calor.", "materials": ["organizador gráfico", "lápices"],
                "differentiation": ActivityDifferentiation(support="Entregue una plantilla con los estados escritos.", extension="Incluya condensación con partículas."),
            },
            {
                "id": "activity-5", "stage_name": "Cierre y evaluación", "title": "Ticket de salida", "duration_minutes": 10,
                "grouping": "individual", "purpose": "Explicar una evidencia observada.",
                "teacher_instructions": ["Entregue el ticket de salida.", "Recoja las respuestas al finalizar."],
                "expected_student_output": "Explicación individual de un cambio de estado observado.", "materials": ["ticket de salida"],
                "differentiation": ActivityDifferentiation(support="Permita usar un banco de palabras.", extension="Pida incorporar temperatura."),
            },
        ],
        materials_summary=["cubo de hielo", "vaso", "hielo", "agua tibia", "film plástico", "hoja de registro", "tarjetas de vocabulario", "organizador gráfico", "ticket de salida", "lápices"],
    )


def water_assessment() -> Assessment:
    return Assessment(
        title="Evaluación breve: cambios de estado del agua",
        instructions=["Responde de forma individual.", "Usa las observaciones realizadas durante la clase."],
        suggested_application_minutes=10,
        total_points=8,
        specification_table=[
            SpecificationRow(learning_objective=OBJECTIVE_ONE, item_count=2, item_ids=["item-1", "item-2"], total_points=5, cognitive_levels=["comprender", "aplicar"]),
            SpecificationRow(learning_objective=OBJECTIVE_TWO, item_count=1, item_ids=["item-3"], total_points=3, cognitive_levels=["comprender"]),
        ],
        items=[
            AssessmentItem(id="item-1", type="selección múltiple", question="En la experiencia con el cubo de hielo, ¿qué cambio observaste?", options=[AssessmentOption(label="A", text="Fusión: el hielo pasó de sólido a líquido."), AssessmentOption(label="B", text="Condensación: el agua pasó de gas a líquido."), AssessmentOption(label="C", text="Evaporación: el agua pasó de líquido a gas.")], correct_option_label="A", expected_answer="Reconoce la fusión observada en el cubo de hielo.", points=2, learning_objective=OBJECTIVE_ONE, cognitive_level="comprender"),
            AssessmentItem(id="item-2", type="respuesta breve", question="El vapor del agua tibia tocó el film frío y aparecieron gotas. Explica qué ocurrió.", expected_answer="Explica que el vapor se enfrió y se condensó formando gotas.", points=3, learning_objective=OBJECTIVE_ONE, cognitive_level="aplicar"),
            AssessmentItem(id="item-3", type="respuesta breve", question="Una bebida fría forma gotas por fuera del vaso. ¿Qué cambio de estado explica esas gotas?", expected_answer="Identifica la condensación y explica el enfriamiento del vapor del aire.", points=3, learning_objective=OBJECTIVE_TWO, cognitive_level="comprender"),
        ],
        rubric=[RubricCriterion(criterion="Explicación de cambios de estado con evidencia", item_ids=["item-1", "item-2", "item-3"], levels=RubricLevels(logrado="Nombra el cambio y lo explica usando evidencia o temperatura.", en_proceso="Nombra parcialmente el cambio, sin conectar bien con la evidencia.", requiere_apoyo="No identifica el cambio de estado o no lo relaciona con la observación."))],
    )


def water_review() -> ReviewReport:
    return ReviewReport(status="clean", summary="El pack de ejemplo fue revisado: objetivos, actividades y evaluación son coherentes.", findings=[], correction=ReviewCorrection(attempted=True, target_agent="assessment", outcome="corrected"))


def water_materials() -> MaterialPack:
    return MaterialPack(
        title="Materiales imprimibles: cambios de estado del agua",
        materials=[
            PrintableMaterial(id="material-1", activity_id="activity-2", source_material_label="hoja de registro", type="tabla_registro", title="Registro de observaciones", student_instructions=["Anota lo que observas y una explicación posible."], content=[PrintableBlock(type="tabla", title="Observaciones", columns=["Experiencia", "Qué observé", "Cambio de estado"], rows=[["Hielo", "", ""], ["Film frío", "", ""]])]),
            PrintableMaterial(id="material-2", activity_id="activity-5", source_material_label="ticket de salida", type="ticket_salida", title="Ticket de salida", student_instructions=["Responde antes de salir."], content=[PrintableBlock(type="preguntas", questions=[{"question": "Describe un cambio de estado que observaste.", "points": 2}])]),
        ],
        coverage=[MaterialCoverage(activity_id="activity-2", source_material_label="hoja de registro", fulfillment="material_generado", material_id="material-1"), MaterialCoverage(activity_id="activity-5", source_material_label="ticket de salida", fulfillment="material_generado", material_id="material-2")],
    )


def mock_audit_report() -> AuditReport:
    return AuditReport(
        overall_status="requiere_atencion",
        source_summary="Informe de auditoría de ejemplo para demostración sin API.",
        parse_confidence="alta",
        parse_notes=[],
        findings=[
            ReviewFinding(id="mock-invalid-oa", severity="bloqueante", responsible_agent="planner", category="curriculum_honesty", artifact_type="plan", artifact_id="CN06 OA 999", description="El código CN06 OA 999 no existe en la fuente curricular de muestra.", suggested_correction="Elimina o reemplaza el código por un OA verificado."),
            ReviewFinding(id="mock-grounding", severity="bloqueante", responsible_agent="assessment", category="grounding", artifact_type="assessment_item", artifact_id="item-2", description="No encontré en las actividades una estación experimental que respalde la evidencia citada por este ítem.", suggested_correction="Usa una observación efectivamente realizada en clase o presenta la situación como una aplicación nueva."),
        ],
    )
