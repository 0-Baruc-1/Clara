"""Run Clara's Reviewer evaluation harness.

Milestone 1 intentionally supports only deterministic mock mode. It must be
invoked with CLARA_MOCK_MODE=true so no result can be mistaken for a real-model
measurement. The real adapter is added in milestone 2.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.runner import run_adversarial_mock, run_mock  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Clara Reviewer evaluation harness.")
    parser.add_argument("--output", type=Path, default=ROOT / "evals" / "reports" / "latest-mock")
    parser.add_argument("--adversarial", action="store_true", help="Ejecuta salidas mock adversariales con métricas esperadas conocidas.")
    args = parser.parse_args()
    if os.getenv("CLARA_MOCK_MODE", "").casefold() not in {"1", "true", "yes"}:
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
