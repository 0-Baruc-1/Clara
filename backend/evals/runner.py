"""Milestone-1 deterministic runner for the evaluation harness itself."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .cases import CASES
from .matcher import match_case
from .metrics import summarize
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
