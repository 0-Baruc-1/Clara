"""Render the frozen hand-adjudicated contract diagnosis from an n=3 report.

This script reads an existing report only.  It never calls the Reviewer, the
curriculum provider, or OpenAI.  The labels below are explicit human semantic
judgments against the raw findings, not a model-generated score.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# One semantic label for each of the eight cases in each of the three completed
# real runs.  ``marginal`` means the finding plausibly describes the injected
# defect, but does not name the OA/claim unambiguously enough to call it clean.
DECLARED_ADJUDICATION = {
    "synthetic-false-alignment-cn-water-oa13": ("clean", "clean", "clean"),
    "synthetic-false-alignment-cn-water-oa15": ("clean", "clean", "clean"),
    "synthetic-false-alignment-cn-energy-oa08": ("clean", "clean", "clean"),
    "synthetic-false-alignment-cn-energy-oa10": ("clean", "clean", "clean"),
    "synthetic-false-alignment-ma-percent-oa03": ("clean", "clean", "clean"),
    "synthetic-false-alignment-ma-percent-oa04": (
        "marginal",
        "marginal",
        "marginal",
    ),
    "synthetic-false-alignment-ma-angle-oa15": ("clean", "clean", "clean"),
    "synthetic-false-alignment-ma-angle-oa20": ("clean", "clean", "clean"),
}

MATERIAL_LABELS = {
    "synthetic-material-gap-cn-water-thermometer": (True, False, True),
    "synthetic-material-gap-cn-water-table": (False, False, False),
    "synthetic-material-gap-cn-energy-battery": (True, False, True),
    "synthetic-material-gap-cn-energy-goggles": (False, False, False),
    "synthetic-material-gap-ma-percent-grid": (True, True, True),
    "synthetic-material-gap-ma-percent-calculator": (False, False, False),
    "synthetic-material-gap-ma-angle-protractor": (True, True, True),
    "synthetic-material-gap-ma-angle-ruler": (False, True, False),
}


def _sum_boolean_labels(labels: dict[str, tuple[bool, bool, bool]]) -> tuple[int, int]:
    return sum(sum(values) for values in labels.values()), len(labels) * 3


def _declared_counts() -> tuple[int, int, int]:
    labels = [label for case_labels in DECLARED_ADJUDICATION.values() for label in case_labels]
    detected = sum(label in {"clean", "marginal"} for label in labels)
    marginal = sum(label == "marginal" for label in labels)
    return detected, len(labels), marginal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renderiza el diagnóstico congelado del contrato de findings sin API."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    declared_detected, declared_total, declared_marginal = _declared_counts()
    materials_detected, materials_total = _sum_boolean_labels(MATERIAL_LABELS)
    aggregate = report["aggregate"]

    lines = [
        "# Diagnóstico congelado del contrato de findings",
        "",
        (
            f"Datos usados: {len(report['runs'])} corridas reales completadas con "
            f"`{report['model']}`. La corrida 4 fue rechazada por `RateLimitError:429`; "
            "no se usó. Este documento no hizo llamadas a OpenAI, al Reviewer ni al proveedor curricular."
        ),
        "",
        "## Conclusión",
        "",
        (
            "Esta corrida no permite medir la calidad del Reviewer con precisión/recall "
            "estrictos. Expuso que el contrato de findings está subespecificado: "
            "`artifact_id` es libre e inestable, las categorías no tienen una ontología "
            "operacional cerrada y no hay regla para distinguir origen de un defecto de "
            "su sitio de manifestación."
        ),
        "",
        (
            "**Titular corregido:** el Reviewer detecta, atribuye correctamente y falla "
            "el match estricto en un único campo sin vocabulario definido: `artifact_id`."
        ),
        "",
        (
            "La precisión no se publica. Cada caso tiene una sola anotación esperada, "
            "mientras el Reviewer emitió múltiples hallazgos potencialmente legítimos: "
            "en la corrida 1 hubo 495 hallazgos no emparejados sobre 68 casos (≈7 por caso). "
            "Por eso, los hallazgos adicionales de un baseline o de la mutación se cuentan "
            "artificialmente como falsos positivos bajo una anotación única. No hay un "
            "denominador de precisión interpretable en esta suite."
        ),
        "",
        "## Descomposición de anclas: OA declarado no trabajado",
        "",
        (
            "Para las 24 instancias de `declared_oa_not_worked` con recall estricto "
            "0/24, se buscó cada ancla esperada en el conjunto de findings emitidos "
            "(no necesariamente en un mismo finding):"
        ),
        "",
        "| Ancla esperada | Presente en los findings emitidos |",
        "|---|---:|",
        "| `responsible_agent=planner` | 24/24 |",
        "| `category=objective_coherence` | 23/24 |",
        "| `artifact_id` canónico (por ejemplo, `CN06 OA 08`) | 1/24 |",
        "",
        (
            "La presencia aislada de agente y categoría es evidencia débil: con ≈7 findings "
            "por caso, ambas pueden aparecer por otros defectos del mismo material. El "
            "`artifact_id` es la señal decisiva. El 0/24 estricto está impulsado por una sola "
            "ancla: el Reviewer nombra el artefacto en vocabulario libre (`activities`, "
            "`PLAN.stages[1]`, `Desarrollo`, etc.) y no con el ID canónico esperado."
        ),
        "",
        "## Detección semántica y adjudicación humana",
        "",
        (
            "La detección semántica fue revisada manualmente contra los findings crudos. "
            "`clean` significa que el finding describe inequívocamente el defecto inyectado. "
            "`marginal` conserva una evidencia plausible, pero ambigua: no se la presenta "
            "como una detección limpia."
        ),
        "",
        "| Familia | Atribución estricta | Detección semántica |",
        "|---|---:|---:|",
        (
            "| OA declarado no trabajado (plan) | 0/24 = 0.000 | "
            f"{declared_detected}/{declared_total}; {declared_total - declared_marginal} limpias, "
            f"{declared_marginal} marginales |"
        ),
        (
            "| Material de actividad faltante (activity) | 1/24 = 0.042 | "
            f"{materials_detected}/{materials_total} = {materials_detected / materials_total:.3f} |"
        ),
        (
            "| Ítem/OA incoherente (assessment_item) | — | recall estricto observable = "
            f"{aggregate['item_not_assessing_claimed_oa']['recall']['mean']:.3f} |"
        ),
        (
            "| Respuesta aritmética incorrecta (assessment_item) | — | recall estricto observable = "
            f"{aggregate['incorrect_arithmetic_answer']['recall']['mean']:.3f} |"
        ),
        "",
        (
            "El patrón sigue el tipo de artefacto esperado —plan 0.000, activity 0.042, "
            "assessment_item 0.606/0.792—, no una supuesta ceguera a errores por ausencia."
        ),
        "",
        "### Matriz: OA declarado no trabajado (24 juicios)",
        "",
        "| Caso | Corrida 1 | Corrida 2 | Corrida 3 |",
        "|---|---|---|---|",
    ]
    for case_id, labels in DECLARED_ADJUDICATION.items():
        lines.append(f"| `{case_id}` | {labels[0]} | {labels[1]} | {labels[2]} |")

    lines.extend(
        [
            "",
            (
                "`synthetic-false-alignment-ma-percent-oa04` es marginal en las tres "
                "corridas: el finding más cercano repite el lenguaje de OA 04 (desempeños "
                "concretos, pictóricos y simbólicos) sin nombrarlo; otro afirma que "
                "`percent-item-2` está correctamente asociado temáticamente a MA06 OA 04. "
                "Es evidencia en tensión, no una confirmación limpia."
            ),
            "",
            "### Matriz: material de actividad faltante",
            "",
            "| Caso | Corrida 1 | Corrida 2 | Corrida 3 |",
            "|---|---|---|---|",
        ]
    )
    for case_id, labels in MATERIAL_LABELS.items():
        values = " | ".join("sí" if label else "no" for label in labels)
        lines.append(f"| `{case_id}` | {values} |")

    lines.extend(
        [
            "",
            "## Casos capturados: corrección de la interpretación",
            "",
            "- `captured-freezer-grounding`: detección y atribución estricta 3/3.",
            (
                "- `captured-cn06-oa15-measurement-gap`: atribución estricta 0/3 porque "
                "el fixture esperaba `plan:CN06 OA 15` atribuido a Planner. Detección "
                "semántica 3/3: los findings aparecieron en `ACTIVIDADES.activities` o "
                "`assessment_item:water-item-2`, describiendo que no había evidencia de "
                "medición ni interpretación al calentar/enfriar agua. Es el mismo defecto "
                "en su manifestación, no una ausencia de detección."
            ),
            "",
            "## Compuerta de precisión",
            "",
            (
                "La supresión fue 4/6, 4/6 y 3/6; hubo 2, 2 y 3 violaciones. Es una señal "
                "de que la política de supresión necesita un contrato verificable, pero no "
                "prueba una ceguera del modelo a hallazgos de ausencia."
            ),
            "",
            "## Near-miss corregido",
            "",
            (
                "En `synthetic-material-gap-cn-energy-battery`, un finding usó categoría "
                "`internal_contradiction` y `artifact_id=energy-test`, igual que el esperado, "
                "pero fue atribuido a `materials` y proyectado como `material:energy-test` "
                "en vez de `designer` / `activity:energy-test`. El detector previo exigía "
                "también igual `artifact_type`, por eso reportaba 0. El detector diagnóstico "
                "ahora lo registra como el único near-miss bajo la regla relajada; el match "
                "estricto no cambió."
            ),
            "",
            "## Único defecto de baseline aprobado",
            "",
            (
                "**Desarrollo: 55 minutos en el plan frente a 3 actividades de 20 minutos = "
                "60 minutos.** Es aritmética determinista y apareció en 3/3 corridas. Es el "
                "único defecto aprobado para corregir si posteriormente se autoriza una "
                "limpieza. Todos los demás hallazgos requieren verificación independiente "
                "contra MINEDUC o una condición determinista."
            ),
            "",
            "## Hallazgo de producto registrado, no implementado",
            "",
            (
                "La evidencia 1/24 del `artifact_id` canónico exige un contrato de findings "
                "con: (1) vocabulario restringido de `artifact_id` derivado de IDs presentes "
                "en el material, (2) ontología de categorías fija y (3) regla explícita "
                "origen-versus-manifestación. Es un hallazgo de esta evaluación; **no se "
                "implementó** el enum, no se modificó el prompt y no se cambió la lógica del Reviewer."
            ),
            "",
            "## Estado",
            "",
            (
                "**Congelado.** No se limpiaron baselines, no se repitieron corridas y no se "
                "agregaron cambios al harness después de este diagnóstico. La evidencia textual "
                "completa está en `manual-label-evidence.md`."
            ),
        ]
    )
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"contract_report_rendered output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
