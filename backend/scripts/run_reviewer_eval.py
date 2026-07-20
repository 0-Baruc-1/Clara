"""Run deterministic calibration or an explicit, repeated real Reviewer measurement."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.runner import run_adversarial_mock, run_mock, run_real  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Clara Reviewer evaluation harness.")
    parser.add_argument("--output", type=Path, default=ROOT / "evals" / "reports" / "latest-mock")
    parser.add_argument("--adversarial", action="store_true", help="Ejecuta salidas mock adversariales con métricas esperadas conocidas.")
    parser.add_argument("--real", action="store_true", help="Mide el Reviewer real. Requiere API key y nunca habilita mock mode.")
    parser.add_argument("--runs", type=int, default=5, help="Repeticiones independientes para --real (por defecto: 5).")
    parser.add_argument("--concurrency", type=int, default=4, help="Casos simultáneos para --real (por defecto: 4).")
    parser.add_argument("--resume", action="store_true", help="Reanuda una medición real incompleta desde su checkpoint compatible.")
    args = parser.parse_args()
    mock_enabled = os.getenv("CLARA_MOCK_MODE", "").casefold() in {"1", "true", "yes"}
    if args.real:
        if mock_enabled:
            raise SystemExit("--real exige CLARA_MOCK_MODE=false o sin definir; no se medirán fixtures mock como si fueran el Reviewer.")
        report = asyncio.run(run_real(args.output, repetitions=args.runs, concurrency=args.concurrency, resume=args.resume))
        print(f"real_reviewer_measurement runs={report['repetitions_completed']}/{report['repetitions_requested']} cases={report['case_counts']['total']} output={args.output}")
        return 0
    if not mock_enabled:
        raise SystemExit("Milestone 1 only runs deterministically with CLARA_MOCK_MODE=true.")
    if args.adversarial:
        report = run_adversarial_mock(args.output)
        print(f"mock_adversarial_harness_calibration scenarios={len(report['scenarios'])} output={args.output}")
    else:
        report = run_mock(args.output)
        counts = report["metrics"]["case_counts"]
        print(f"mock_harness_self_test cases={counts['total']} controls={counts['controls']} gate_cases={counts['audit_gate_cases']} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
