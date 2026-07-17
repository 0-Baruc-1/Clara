"""Typed, hand-authored materials used by the real Reviewer evaluation adapter.

The cases module names the mutations and ground truth.  This module provides the
actual lesson artifacts that the production Reviewer receives; it never asks an
LLM to manufacture an evaluation fixture.
"""
from __future__ import annotations

from copy import deepcopy

from app.models.teaching_pack import (
    ActivityDifferentiation,
    ActivityGuide,
    Assessment,
    AssessmentItem,
    AssessmentOption,
    CurriculumAlignment,
    CurriculumObjective,
    LessonPlan,
    LessonStage,
    RubricCriterion,
    RubricLevels,
    SpecificationRow,
    ClassroomActivity,
)

from .cases import EvaluationCase


_SOURCE = "https://www.curriculumnacional.cl/"


def _objective(code: str, description: str) -> CurriculumObjective:
    return CurriculumObjective(code=code, description=description, source=_SOURCE)


def _activity(
    activity_id: str,
    stage_name: str,
    title: str,
    purpose: str,
    materials: list[str],
) -> ClassroomActivity:
    return ClassroomActivity(
        id=activity_id,
        stage_name=stage_name,
        title=title,
        duration_minutes=20,
        grouping="parejas",
        purpose=purpose,
        teacher_instructions=["Presenta la consigna y acompaña el trabajo en parejas."],
        expected_student_output="Registro breve con una explicación basada en la actividad.",
        materials=materials,
        differentiation=ActivityDifferentiation(
            support="Entrega un ejemplo guiado y vocabulario de apoyo.",
            extension="Pide justificar la respuesta con una segunda evidencia.",
        ),
    )


def _item(item_id: str, objective: str, question: str, answer: str, points: int = 2) -> AssessmentItem:
    return AssessmentItem(
        id=item_id,
        type="respuesta breve",
        question=question,
        options=[],
        expected_answer=answer,
        points=points,
        learning_objective=objective,
        cognitive_level="aplicar",
    )


def _pack(
    *,
    subject: str,
    objective_data: list[tuple[str, str]],
    activity_data: list[tuple[str, str]],
    item_data: list[tuple[str, str]],
    materials: list[str],
) -> tuple[LessonPlan, ActivityGuide, Assessment]:
    objectives = [_objective(code, wording) for code, wording in objective_data]
    objective_codes = [objective.code for objective in objectives]
    plan = LessonPlan(
        title=f"Secuencia de {subject}",
        subject=subject,
        grade_level="6° básico",
        duration_minutes=90,
        curriculum_alignment=CurriculumAlignment(status="aligned", objectives=objectives),
        learning_objectives=objective_codes,
        key_concepts=["observar", "explicar", "representar"],
        prerequisite_knowledge=["Registrar observaciones sencillas."],
        materials=materials,
        stages=[
            LessonStage(name="Inicio", duration_minutes=15, purpose="Activar conocimientos previos.", formative_check="Explicación oral breve."),
            LessonStage(name="Desarrollo", duration_minutes=55, purpose="Investigar y aplicar el objetivo mediante evidencia.", formative_check="Revisión de registros."),
            LessonStage(name="Cierre", duration_minutes=20, purpose="Comunicar una conclusión basada en evidencia.", formative_check="Ticket de salida."),
        ],
    )
    activities = ActivityGuide(
        title="Guía de actividades",
        overview="Actividades directamente vinculadas con los objetivos del plan.",
        targeted_learning_objectives=objective_codes,
        activities=[
            _activity(activity_id, "Desarrollo", title, "Investigar el objetivo mediante una tarea observable y registrar evidencia.", materials)
            for activity_id, title in activity_data
        ],
        materials_summary=materials,
    )
    items = [_item(item_id, objective_codes[index % len(objective_codes)], question, "Criterio correcto y observable.") for index, (item_id, question) in enumerate(item_data)]
    assessment = Assessment(
        title="Instrumento de evaluación",
        instructions=["Responde usando la evidencia trabajada en clase."],
        suggested_application_minutes=15,
        total_points=sum(item.points for item in items),
        specification_table=[
            SpecificationRow(
                learning_objective=code,
                item_count=len([item for item in items if item.learning_objective == code]),
                item_ids=[item.id for item in items if item.learning_objective == code],
                total_points=sum(item.points for item in items if item.learning_objective == code),
                cognitive_levels=["aplicar"],
            )
            for code in objective_codes
        ],
        items=items,
        rubric=[
            RubricCriterion(
                criterion="Explica su respuesta con evidencia de la actividad.",
                item_ids=[item.id for item in items],
                levels=RubricLevels(
                    logrado="Relaciona correctamente la respuesta con evidencia.",
                    en_proceso="Relaciona parcialmente la respuesta con evidencia.",
                    requiere_apoyo="No relaciona aún la respuesta con evidencia.",
                ),
            )
        ],
    )
    return plan, activities, assessment


def _baseline(baseline_id: str) -> tuple[LessonPlan, ActivityGuide, Assessment]:
    if baseline_id == "cn_water_states_v1":
        return _pack(
            subject="Ciencias Naturales",
            objective_data=[
                ("CN06 OA 13", "Investigar y explicar que la materia cambia de estado cuando se modifica la temperatura."),
                ("CN06 OA 15", "Medir y registrar datos para comunicar conclusiones de una investigación científica escolar."),
            ],
            activity_data=[
                ("water-observe", "Observar hielo que se derrite en un recipiente del aula"),
                ("water-record", "Registrar los cambios de estado observados"),
                ("water-exit", "Explicar un cambio de estado con evidencia"),
            ],
            item_data=[
                ("water-item-1", "Explica qué ocurrió con el hielo observado durante la actividad."),
                ("water-item-2", "Relaciona el cambio observado con una variación de temperatura."),
                ("water-item-3", "Usa tu registro para justificar una conclusión."),
            ],
            materials=["hielo", "recipiente", "tabla de registro", "termómetro"],
        )
    if baseline_id == "cn_energy_v1":
        return _pack(
            subject="Ciencias Naturales",
            objective_data=[
                ("CN06 OA 08", "Explicar formas de energía a partir de situaciones del entorno."),
                ("CN06 OA 10", "Investigar la transferencia de energía térmica mediante experiencias sencillas."),
            ],
            activity_data=[("energy-predict", "Predecir transferencia de calor"), ("energy-test", "Comparar materiales en una experiencia térmica"), ("energy-exit", "Explicar una transferencia observada")],
            item_data=[("energy-item-1", "Explica la transferencia de calor observada."), ("energy-item-2", "Relaciona el material con la evidencia de la experiencia."), ("energy-item-3", "Propone una conclusión a partir del registro.")],
            materials=["vasos", "agua tibia", "cucharas", "tabla de registro", "pilas", "circuito", "lentes de seguridad"],
        )
    if baseline_id == "ma_percentages_v1":
        return _pack(
            subject="Matemática",
            objective_data=[
                ("MA06 OA 03", "Demostrar que comprenden el concepto de razón de manera concreta, pictórica y simbólica."),
                ("MA06 OA 04", "Demostrar que comprenden el concepto de porcentaje de manera concreta, pictórica y simbólica."),
            ],
            activity_data=[("percent-model", "Representar porcentajes con cuadrículas"), ("percent-problems", "Resolver problemas de porcentaje"), ("percent-exit", "Justificar una razón y un porcentaje")],
            item_data=[("percent-item-1", "Calcula el 25% de 80."), ("percent-item-2", "Calcula el 15% de 200."), ("percent-item-3", "Explica por qué la razón 1:4 equivale a 25%.")],
            materials=["cuadrícula porcentual", "calculadora", "ficha de problemas"],
        )
    if baseline_id == "ma_geometry_v1":
        return _pack(
            subject="Matemática",
            objective_data=[
                ("MA06 OA 15", "Construir y medir ángulos con instrumentos geométricos."),
                ("MA06 OA 20", "Resolver problemas que involucren medición de ángulos."),
            ],
            activity_data=[("angle-build", "Construir ángulos con regla"), ("angle-measure", "Medir ángulos con transportador"), ("angle-exit", "Explicar una medición")],
            item_data=[("angle-item-1", "Calcula el suplemento de 120°."), ("angle-item-2", "Determina la suma de los ángulos interiores de un triángulo."), ("angle-item-3", "Explica cómo medirías un ángulo recto.")],
            materials=["transportador", "regla", "papel"],
        )
    raise ValueError(f"Baseline desconocido: {baseline_id}")


def _activity_by_id(activities: ActivityGuide, activity_id: str) -> ClassroomActivity:
    return next(activity for activity in activities.activities if activity.id == activity_id)


def _item_by_id(assessment: Assessment, item_id: str) -> AssessmentItem:
    return next(item for item in assessment.items if item.id == item_id)


def build_case_material(case: EvaluationCase) -> tuple[LessonPlan, ActivityGuide, Assessment]:
    """Return a typed baseline plus the case's one hand-authored injected defect."""
    plan, activities, assessment = deepcopy(_baseline(case.baseline_id))
    if not case.injected_errors:
        return plan, activities, assessment
    issue = case.injected_errors[0]
    error_class = issue.error_class
    if error_class == "fabricated_oa":
        code = issue.target.artifact_id
        plan.curriculum_alignment.objectives.append(_objective(code, "Objetivo declarado para verificar su existencia."))
        plan.learning_objectives.append(code)
        activities.targeted_learning_objectives.append(code)
        return plan, activities, assessment
    if error_class == "declared_oa_not_worked":
        code = issue.target.artifact_id
        for activity in activities.activities:
            activity.purpose = "Copiar definiciones sin investigar, medir ni aplicar el objetivo declarado."
            activity.teacher_instructions = ["Pide copiar una definición del pizarrón."]
            activity.expected_student_output = "Copia literal de una definición."
        return plan, activities, assessment
    if error_class == "item_not_assessing_claimed_oa":
        item = _item_by_id(assessment, issue.target.artifact_id)
        item.question = "¿Cuál es tu color favorito? Escribe una oración."
        item.expected_answer = "Cualquier respuesta sobre una preferencia personal."
        return plan, activities, assessment
    if error_class == "incorrect_arithmetic_answer":
        item = _item_by_id(assessment, issue.target.artifact_id)
        item.expected_answer = "30 (respuesta correcta declarada)."
        # The wording is deliberately explicit so an arithmetic failure is attributable.
        if "25%" not in item.question and "15%" not in item.question and "razón" not in item.question and "ángulo" not in item.question:
            item.question = "Calcula 25% de 80."
        return plan, activities, assessment
    if error_class == "activity_material_gap":
        activity = _activity_by_id(activities, issue.target.artifact_id)
        missing = {
            "thermometer": "termómetro",
            "table": "tabla de registro",
            "battery": "pilas y circuito",
            "goggles": "lentes de seguridad",
            "grid": "cuadrícula porcentual",
            "calculator": "calculadora",
            "protractor": "transportador",
            "ruler": "regla",
        }
        key = next((name for name in missing if name in issue.id), "termómetro")
        label = missing[key]
        activity.materials = [label]
        activity.teacher_instructions = [f"Entrega {label} a cada pareja antes de comenzar la actividad."]
        plan.materials = [material for material in plan.materials if material != label]
        activities.materials_summary = sorted({material for item in activities.activities for material in item.materials})
        return plan, activities, assessment
    if error_class == "grounding_absent_experiment":
        item = _item_by_id(assessment, issue.target.artifact_id) if any(candidate.id == issue.target.artifact_id for candidate in assessment.items) else assessment.items[0]
        item.id = issue.target.artifact_id
        item.question = "Según la estación experimental final, ¿qué midió el curso en una cubetera dentro de un freezer a 8°C?"
        item.expected_answer = "Usa la medición de la cubetera realizada por el curso en la estación experimental final."
        return plan, activities, assessment
    raise ValueError(f"Clase de error no soportada: {error_class}")
