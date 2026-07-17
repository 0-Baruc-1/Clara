"""Runners for deterministic harness checks and repeated production measurements."""
from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .adversarial import SCENARIOS, outputs_for
from .cases import CASES
from .matcher import match_case
from .metrics import PRIMARY_CLASSES, summarize
from .mock_adapter import DeterministicMockReviewer


def run_mock(output_dir: Path) -> dict[str, object]:
    adapter = DeterministicMockReviewer()
    results = {case.id: match_case(case, adapter.run(case)) for case in CASES}
    report = {
        "mode": "mock_harness_self_test",
        "warning": "Este resultado prueba el harness; no mide el desempeño del Reviewer ni de un modelo.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": summarize(results),
        "cases": [case.to_dict() for case in CASES],
        "match_results": {case_id: asdict(result) for case_id, result in results.items()},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Clara Reviewer Evaluation — mock harness self-test",
        "",
        "This is deterministic harness verification, not a model-performance result.",
        "",
        f"Cases: {report['metrics']['case_counts']['total']}",
        f"Controls: {report['metrics']['case_counts']['controls']}",
        f"Gate cases: {report['metrics']['case_counts']['audit_gate_cases']}",
    ]
    (output_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return report


def run_adversarial_mock(output_dir: Path) -> dict[str, object]:
    """Run known-bad mock outputs; these calibrate the metric instrument."""
    scenarios: dict[str, object] = {}
    for scenario in SCENARIOS:
        outputs = outputs_for(scenario)
        results = {case.id: match_case(case, outputs[case.id]) for case in CASES}
        scenarios[scenario] = summarize(results)
    report = {
        "mode": "mock_adversarial_harness_calibration",
        "warning": "Estos escenarios prueban que el harness detecta fallas conocidas; no son métricas del Reviewer real.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenarios": scenarios,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Clara Reviewer Evaluation — adversarial mock calibration", ""]
    for name, metrics in scenarios.items():
        lines.append(f"- {name}: {json.dumps(metrics['model_reasoning_score'], ensure_ascii=False)}")
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def _numeric_summary(values: list[float | None]) -> dict[str, float | int | None]:
    finite = [value for value in values if value is not None]
    if not finite:
        return {"runs": 0, "mean": None, "sample_standard_deviation": None}
    mean = sum(finite) / len(finite)
    deviation = None if len(finite) < 2 else math.sqrt(sum((value - mean) ** 2 for value in finite) / (len(finite) - 1))
    return {"runs": len(finite), "mean": mean, "sample_standard_deviation": deviation}


def _aggregate_real_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate run-level rates; do not pool repeated calls as independent cases."""
    metric_paths: dict[str, list[dict[str, object]]] = {error_class: [] for error_class in (*PRIMARY_CLASSES, "model_reasoning_score")}
    for run in runs:
        metrics = run["metrics"]
        for error_class in metric_paths:
            metric_paths[error_class].append(metrics["model_reasoning_score"] if error_class == "model_reasoning_score" else metrics["per_error_class"][error_class])
    return {
        name: {
            metric: _numeric_summary([row[metric] for row in rows])
            for metric in ("precision", "recall", "control_false_positive_rate", "severity_accuracy_among_true_positives")
        }
        for name, rows in metric_paths.items()
    }


async def run_real(output_dir: Path, *, repetitions: int) -> dict[str, object]:
    """Measure the real, existing Reviewer.  This function never enables mock mode."""
    # Keep deterministic calibration importable even when the OpenAI SDK is not
    # installed in a lightweight test environment.
    from app.core.config import settings
    from .real_adapter import ProductionReviewerAdapter
    if repetitions < 1:
        raise ValueError("Las repeticiones deben ser al menos una.")
    adapter = ProductionReviewerAdapter()
    runs: list[dict[str, object]] = []
    for run_number in range(1, repetitions + 1):
        results = {case.id: match_case(case, await adapter.run(case)) for case in CASES}
        runs.append({
            "run": run_number,
            "metrics": summarize(results),
            "match_results": {case_id: asdict(result) for case_id, result in results.items()},
        })
    report = {
        "mode": "real_reviewer_measurement",
        "warning": "Las repeticiones son llamadas independientes al Reviewer. Las tasas agregadas son medias por corrida, no casos agrupados.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": settings.reviewer_model or settings.openai_model,
        "repetitions": repetitions,
        "case_counts": summarize({case.id: match_case(case, []) for case in CASES})["case_counts"],
        "runs": runs,
        "aggregate": _aggregate_real_runs(runs),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Clara Reviewer Evaluation — medición real",
        "",
        f"Modelo: {report['model']}",
        f"Repeticiones independientes: {repetitions}",
        "Las métricas son media y desviación estándar muestral entre corridas; no se agrupan llamadas repetidas como casos adicionales.",
    ]
    (output_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return report
