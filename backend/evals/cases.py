"""Hand-authored ground truth for Reviewer measurement.

These fixtures are deliberately data, not LLM-generated examples. A helper only
removes repeated dataclass boilerplate; every baseline, mutation, target and
expected finding is enumerated below for review.
"""
from __future__ import annotations

from .schemas import ArtifactAnchor, EvaluationCase, ExpectedFinding, InjectedError, MaterialMutation


def _mutation(path: str, value: object, explanation: str, operation: str = "replace") -> MaterialMutation:
    return MaterialMutation(path=path, operation=operation, value=value, explanation=explanation)  # type: ignore[arg-type]


def _issue(
    issue_id: str,
    error_class: str,
    artifact_type: str,
    artifact_id: str,
    category: str,
    agent: str,
    severity: str = "importante",
    action: str = "emit",
    explanation: str = "Error inyectado manualmente.",
) -> tuple[InjectedError, ExpectedFinding]:
    anchor = ArtifactAnchor(artifact_type=artifact_type, artifact_id=artifact_id)  # type: ignore[arg-type]
    return (
        InjectedError(id=issue_id, error_class=error_class, target=anchor, explanation=explanation),  # type: ignore[arg-type]
        ExpectedFinding(
            issue_id=issue_id,
            error_class=error_class,  # type: ignore[arg-type]
            action=action,  # type: ignore[arg-type]
            category=category,  # type: ignore[arg-type]
            target=anchor,
            responsible_agent=agent,  # type: ignore[arg-type]
            minimum_severity=severity,  # type: ignore[arg-type]
        ),
    )


def _error_case(
    case_id: str,
    title: str,
    baseline_id: str,
    mutation: MaterialMutation,
    issue: tuple[InjectedError, ExpectedFinding],
    *,
    provenance: str = "synthetic",
    kind: str = "error",
    activity_confidence: str = "alta",
    assessment_confidence: str = "alta",
) -> EvaluationCase:
    return EvaluationCase(
        id=case_id,
        title=title,
        provenance=provenance,  # type: ignore[arg-type]
        kind=kind,  # type: ignore[arg-type]
        baseline_id=baseline_id,
        material_mutations=(mutation,),
        injected_errors=(issue[0],),
        expected=(issue[1],),
        activity_confidence=activity_confidence,  # type: ignore[arg-type]
        assessment_confidence=assessment_confidence,  # type: ignore[arg-type]
    )


FALSE_ALIGNMENT_ROWS = (
    ("cn-water-oa13", "cn_water_states_v1", "CN06 OA 13", "Se declara OA 13, pero se eliminan las experiencias de cambios de estado."),
    ("cn-water-oa15", "cn_water_states_v1", "CN06 OA 15", "Se declara OA 15, pero ninguna actividad mide ni interpreta datos."),
    ("cn-energy-oa08", "cn_energy_v1", "CN06 OA 08", "Se declara OA 08, pero se reemplazan las actividades por copia de definiciones."),
    ("cn-energy-oa10", "cn_energy_v1", "CN06 OA 10", "Se declara OA 10, pero no hay experimento de transferencia de calor."),
    ("ma-percent-oa03", "ma_percentages_v1", "MA06 OA 03", "Se declara razón, pero las actividades solo piden identificar porcentajes."),
    ("ma-percent-oa04", "ma_percentages_v1", "MA06 OA 04", "Se declara porcentaje, pero se eliminan representaciones y cálculos porcentuales."),
    ("ma-angle-oa15", "ma_geometry_v1", "MA06 OA 15", "Se declara construcción de ángulos, pero las actividades solo nombran ángulos."),
    ("ma-angle-oa20", "ma_geometry_v1", "MA06 OA 20", "Se declara medición con transportador, pero no se mide ningún ángulo."),
)

ITEM_ALIGNMENT_ROWS = (
    ("cn-water-item1", "cn_water_states_v1", "water-item-1", "El ítem pide recordar una definición sin evaluar la explicación del OA."),
    ("cn-water-item2", "cn_water_states_v1", "water-item-2", "El ítem pregunta el color del vaso y mantiene una etiqueta de OA de cambios de estado."),
    ("cn-energy-item1", "cn_energy_v1", "energy-item-1", "El ítem pide nombrar una fuente de energía, no la transferencia de calor declarada."),
    ("cn-energy-item2", "cn_energy_v1", "energy-item-2", "El ítem evalúa ortografía y conserva la etiqueta de OA científico."),
    ("ma-percent-item1", "ma_percentages_v1", "percent-item-1", "El ítem calcula una suma entera y afirma medir porcentaje."),
    ("ma-percent-item2", "ma_percentages_v1", "percent-item-2", "El ítem pregunta una opinión sobre matemáticas y conserva OA 04."),
    ("ma-angle-item1", "ma_geometry_v1", "angle-item-1", "El ítem pide identificar una figura, no construir ni medir ángulos."),
    ("ma-angle-item2", "ma_geometry_v1", "angle-item-2", "El ítem evalúa lectura de una historia y conserva OA 20."),
)

ARITHMETIC_ROWS = (
    ("ma-percent-answer-1", "ma_percentages_v1", "percent-item-1", "25% de 80 se marca incorrectamente como 30."),
    ("ma-percent-answer-2", "ma_percentages_v1", "percent-item-2", "El resultado de 15% de 200 se marca incorrectamente como 20."),
    ("ma-percent-answer-3", "ma_percentages_v1", "percent-item-3", "Una razón 1:4 se transforma incorrectamente en 40%."),
    ("ma-percent-answer-4", "ma_percentages_v1", "percent-item-1", "60% de 50 se marca incorrectamente como 20."),
    ("ma-angle-answer-1", "ma_geometry_v1", "angle-item-1", "El suplemento de 120° se marca incorrectamente como 70°."),
    ("ma-angle-answer-2", "ma_geometry_v1", "angle-item-2", "La suma interior de un triángulo se marca incorrectamente como 360°."),
    ("ma-angle-answer-3", "ma_geometry_v1", "angle-item-3", "Un ángulo recto se marca incorrectamente como 100°."),
    ("ma-angle-answer-4", "ma_geometry_v1", "angle-item-1", "35° + 55° se marca incorrectamente como 80°."),
)

MATERIAL_GAP_ROWS = (
    ("cn-water-thermometer", "cn_water_states_v1", "water-observe", "La actividad exige termómetro, ausente de recursos del plan."),
    ("cn-water-table", "cn_water_states_v1", "water-record", "La actividad exige tabla de registro, ausente de recursos del plan."),
    ("cn-energy-battery", "cn_energy_v1", "energy-test", "La actividad exige pilas y circuito, ausentes de recursos del plan."),
    ("cn-energy-goggles", "cn_energy_v1", "energy-predict", "La actividad exige lentes de seguridad, ausentes de recursos del plan."),
    ("ma-percent-grid", "ma_percentages_v1", "percent-model", "La actividad exige cuadrícula porcentual, ausente de recursos del plan."),
    ("ma-percent-calculator", "ma_percentages_v1", "percent-problems", "La actividad exige calculadora, ausente de recursos del plan."),
    ("ma-angle-protractor", "ma_geometry_v1", "angle-measure", "La actividad exige transportador, ausente de recursos del plan."),
    ("ma-angle-ruler", "ma_geometry_v1", "angle-build", "La actividad exige regla, ausente de recursos del plan."),
)

FABRICATED_ROWS = (
    ("cn-water-999", "cn_water_states_v1", "CN06 OA 99"),
    ("cn-water-00", "cn_water_states_v1", "CN06 OA 00"),
    ("cn-energy-77", "cn_energy_v1", "CN06 OA 77"),
    ("cn-energy-91", "cn_energy_v1", "CN06 OA 91"),
    ("ma-percent-99", "ma_percentages_v1", "MA06 OA 99"),
    ("ma-percent-00", "ma_percentages_v1", "MA06 OA 00"),
    ("ma-angle-77", "ma_geometry_v1", "MA06 OA 77"),
    ("ma-angle-91", "ma_geometry_v1", "MA06 OA 91"),
)


def _synthetic_cases() -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    for suffix, baseline, code, explanation in FALSE_ALIGNMENT_ROWS:
        issue = _issue(f"false-alignment-{suffix}", "declared_oa_not_worked", "plan", code, "objective_coherence", "planner", explanation=explanation)
        cases.append(_error_case(f"synthetic-false-alignment-{suffix}", "OA declarado pero no trabajado", baseline, _mutation("activities", "Actividades no relacionadas con el OA.", explanation), issue))
    for suffix, baseline, item_id, explanation in ITEM_ALIGNMENT_ROWS:
        issue = _issue(f"item-alignment-{suffix}", "item_not_assessing_claimed_oa", "assessment_item", item_id, "objective_coherence", "assessment", explanation=explanation)
        cases.append(_error_case(f"synthetic-item-alignment-{suffix}", "Ítem no evalúa su OA declarado", baseline, _mutation(f"assessment.items[{item_id}].question", explanation, explanation), issue))
    for suffix, baseline, item_id, explanation in ARITHMETIC_ROWS:
        issue = _issue(f"arithmetic-{suffix}", "incorrect_arithmetic_answer", "assessment_item", item_id, "internal_contradiction", "assessment", explanation=explanation)
        cases.append(_error_case(f"synthetic-arithmetic-{suffix}", "Respuesta aritmética incorrecta", baseline, _mutation(f"assessment.items[{item_id}].expected_answer", explanation, explanation), issue))
    for suffix, baseline, activity_id, explanation in MATERIAL_GAP_ROWS:
        issue = _issue(f"material-gap-{suffix}", "activity_material_gap", "activity", activity_id, "internal_contradiction", "designer", explanation=explanation)
        cases.append(_error_case(f"synthetic-material-gap-{suffix}", "Actividad con recurso ausente", baseline, _mutation(f"activities[{activity_id}].materials", explanation, explanation, "append"), issue))
    for suffix, baseline, code in FABRICATED_ROWS:
        issue = _issue(f"fabricated-{suffix}", "fabricated_oa", "plan", code, "curriculum_honesty", "planner", "bloqueante", explanation=f"Se declara el código inexistente {code}.")
        cases.append(_error_case(f"synthetic-fabricated-oa-{suffix}", "Código OA fabricado", baseline, _mutation("lesson_plan.curriculum_alignment.objectives", code, f"Se agrega {code}.", "append"), issue))
    return cases


def _controls() -> list[EvaluationCase]:
    baseline_order = (
        "cn_water_states_v1", "cn_energy_v1", "ma_percentages_v1", "ma_geometry_v1",
        "cn_water_states_v1", "ma_percentages_v1", "cn_energy_v1", "ma_geometry_v1",
        "cn_water_states_v1", "ma_percentages_v1",
    )
    return [
        EvaluationCase(
            id=f"control-{index + 1:02d}",
            title="Material correcto sin error inyectado",
            provenance="synthetic",
            kind="control",
            baseline_id=baseline,
        )
        for index, baseline in enumerate(baseline_order)
    ]


def _captured_cases() -> list[EvaluationCase]:
    freezer = _issue(
        "captured-freezer-grounding",
        "grounding_absent_experiment",
        "assessment_item",
        "water-item-freezer",
        "grounding",
        "assessment",
        "bloqueante",
        explanation="El ítem afirma que el curso midió agua en una cubetera dentro de un freezer, experiencia inexistente en la guía.",
    )
    oa15 = _issue(
        "captured-cn06-oa15-measurement",
        "declared_oa_not_worked",
        "plan",
        "CN06 OA 15",
        "objective_coherence",
        "planner",
        explanation="El termómetro es opcional y ninguna actividad ni ítem exige medir o interpretar datos, pese a declarar CN06 OA 15.",
    )
    return [
        _error_case(
            "captured-freezer-grounding",
            "Capturado: evaluación inventa experiencia en freezer",
            "cn_water_states_v1",
            _mutation("assessment.items[water-item-freezer]", "El curso midió una cubetera en el freezer a 8°C.", "Falla observada en una ejecución real.", "append"),
            freezer,
            provenance="captured",
        ),
        _error_case(
            "captured-cn06-oa15-measurement-gap",
            "Capturado: CN06 OA 15 declarado sin evidencia de medición",
            "cn_water_states_v1",
            _mutation("lesson_plan.materials", "Se elimina el termómetro obligatorio y toda exigencia de medición.", "Falla observada en una ejecución real."),
            oa15,
            provenance="captured",
        ),
    ]


def _gate_cases() -> list[EvaluationCase]:
    sources = [
        ("declared_oa_not_worked", "cn_water_states_v1", "CN06 OA 13", "plan", "objective_coherence", "planner"),
        ("declared_oa_not_worked", "cn_energy_v1", "CN06 OA 10", "plan", "objective_coherence", "planner"),
        ("declared_oa_not_worked", "ma_percentages_v1", "MA06 OA 04", "plan", "objective_coherence", "planner"),
        ("item_not_assessing_claimed_oa", "cn_water_states_v1", "water-item-2", "assessment_item", "objective_coherence", "assessment"),
        ("item_not_assessing_claimed_oa", "cn_energy_v1", "energy-item-2", "assessment_item", "objective_coherence", "assessment"),
        ("item_not_assessing_claimed_oa", "ma_geometry_v1", "angle-item-2", "assessment_item", "objective_coherence", "assessment"),
        ("fabricated_oa", "ma_percentages_v1", "MA06 OA 99", "plan", "curriculum_honesty", "planner"),
        ("fabricated_oa", "cn_energy_v1", "CN06 OA 99", "plan", "curriculum_honesty", "planner"),
    ]
    cases: list[EvaluationCase] = []
    for index, (error_class, baseline, artifact_id, artifact_type, category, agent) in enumerate(sources, start=1):
        is_absence = error_class != "fabricated_oa"
        for confidence in ("alta", "baja"):
            action = "suppress" if is_absence and confidence == "baja" else "emit"
            issue = _issue(
                f"gate-{index}-{confidence}", error_class, artifact_type, artifact_id, category, agent,
                "bloqueante" if error_class == "fabricated_oa" else "importante", action,
                explanation="Caso explícito para medir la compuerta de precisión.",
            )
            cases.append(_error_case(
                f"gate-{index:02d}-{confidence}",
                f"Compuerta de precisión: {error_class} con confianza {confidence}",
                baseline,
                _mutation("harness.gate", confidence, "La confianza de parse es parte del ground truth."),
                issue,
                kind="audit_gate",
                activity_confidence=confidence,
                assessment_confidence=confidence,
            ))
    return cases


CASES: tuple[EvaluationCase, ...] = tuple(_synthetic_cases() + _controls() + _captured_cases() + _gate_cases())


def cases_by_id() -> dict[str, EvaluationCase]:
    return {case.id: case for case in CASES}
