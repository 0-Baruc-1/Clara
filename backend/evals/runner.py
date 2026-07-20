"""Runners for deterministic harness checks and repeated production measurements."""
from __future__ import annotations

import json
import math
import asyncio
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


def _real_report(*, runs: list[dict[str, object]], repetitions: int, concurrency: int, completed: bool) -> dict[str, object]:
    from app.core.config import settings
    return {
        "mode": "real_reviewer_measurement",
        "warning": "Las repeticiones son llamadas independientes al Reviewer. Las tasas agregadas son medias por corrida, no casos agrupados.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": settings.reviewer_model or settings.openai_model,
        "repetitions_requested": repetitions,
        "repetitions_completed": len(runs),
        "bounded_concurrency": concurrency,
        "concurrency_by_run": {str(run["run"]): run.get("concurrency", concurrency) for run in runs},
        "completed": completed,
        "case_counts": summarize({case.id: match_case(case, []) for case in CASES})["case_counts"],
        "runs": runs,
        "aggregate": _aggregate_real_runs(runs) if runs else {},
    }


def _write_real_report(output_dir: Path, report: dict[str, object]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CaseEvaluationError(RuntimeError):
    """Safe evaluation infrastructure error with a case locator, never API text."""

    def __init__(self, *, case_id: str, cause: Exception) -> None:
        super().__init__(type(cause).__name__)
        self.case_id = case_id
        error_type = getattr(cause, "error_type", type(cause).__name__)
        status_code = getattr(cause, "status_code", None)
        self.cause_type = f"{error_type}:{status_code}" if status_code is not None else error_type


async def run_real(output_dir: Path, *, repetitions: int, concurrency: int = 4, resume: bool = False) -> dict[str, object]:
    """Measure the real, existing Reviewer.  This function never enables mock mode."""
    # Keep deterministic calibration importable even when the OpenAI SDK is not
    # installed in a lightweight test environment.
    from .real_adapter import ProductionReviewerAdapter

    if repetitions < 1:
        raise ValueError("Las repeticiones deben ser al menos una.")
    if concurrency < 1:
        raise ValueError("La concurrencia debe ser al menos una.")
    adapter = ProductionReviewerAdapter()
    runs: list[dict[str, object]] = []
    report_path = output_dir / "report.json"
    if resume and report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous.get("mode") != "real_reviewer_measurement":
            raise ValueError("El reporte existente no es una medición real que se pueda reanudar.")
        if previous.get("repetitions_requested") != repetitions:
            raise ValueError("Para reanudar, las repeticiones solicitadas deben coincidir con el checkpoint.")
        runs = list(previous.get("runs", []))
    for run_number in range(len(runs) + 1, repetitions + 1):
        print(f"real_run_started run={run_number}/{repetitions}", flush=True)
        semaphore = asyncio.Semaphore(concurrency)

        async def evaluate(case_number: int, case: object) -> tuple[str, object]:
            # EvaluationCase is kept as object here only to keep the closure tiny;
            # CASES supplies the concrete contract.
            try:
                async with semaphore:
                    return case.id, match_case(case, await adapter.run(case))  # type: ignore[attr-defined]
            except Exception as error:
                # Diagnostics deliberately omit request text, responses and credentials.
                print(f"real_run_failed run={run_number}/{repetitions} case={case_number}/{len(CASES)} case_id={case.id} error_type={type(error).__name__}", flush=True)  # type: ignore[attr-defined]
                raise CaseEvaluationError(case_id=case.id, cause=error) from error  # type: ignore[attr-defined]
        try:
            pairs = await asyncio.gather(*(evaluate(case_number, case) for case_number, case in enumerate(CASES, start=1)))
        except Exception as error:
            failed = _real_report(runs=runs, repetitions=repetitions, concurrency=concurrency, completed=False)
            failed["failure"] = {
                "run": run_number,
                "case_id": getattr(error, "case_id", None),
                "error_type": getattr(error, "cause_type", type(error).__name__),
            }
            _write_real_report(output_dir, failed)
            raise
        results = dict(pairs)
        print(f"real_run_completed run={run_number}/{repetitions}", flush=True)
        runs.append({
            "run": run_number,
            "concurrency": concurrency,
            "metrics": summarize(results),
            "match_results": {case_id: asdict(result) for case_id, result in results.items()},
        })
        _write_real_report(output_dir, _real_report(runs=runs, repetitions=repetitions, concurrency=concurrency, completed=False))
    report = _real_report(runs=runs, repetitions=repetitions, concurrency=concurrency, completed=True)
    _write_real_report(output_dir, report)
    summary = [
        "# Clara Reviewer Evaluation — medición real",
        "",
        f"Modelo: {report['model']}",
        f"Repeticiones independientes: {repetitions}",
        f"Concurrencia acotada: {concurrency}",
        "Las métricas son media y desviación estándar muestral entre corridas; no se agrupan llamadas repetidas como casos adicionales.",
    ]
    (output_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return report
