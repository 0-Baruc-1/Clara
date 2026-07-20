"""Extract existing raw findings for manual evaluation-harness adjudication.

This is deliberately read-only with respect to the API and Reviewer. It turns a
saved real-run report into a human-labeling worksheet.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.cases import cases_by_id  # noqa: E402


CLASSES = {"declared_oa_not_worked", "activity_material_gap"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrae evidencia cruda existente, sin llamadas API.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    cases = cases_by_id()
    lines = ["# Evidencia cruda para etiquetado manual", "", "No ejecutar el Reviewer ni inferir matches desde el texto: esta hoja conserva los hallazgos emitidos.", ""]
    for error_class in sorted(CLASSES):
        lines.extend([f"## {error_class}", ""])
        for case in (case for case in cases.values() if case.kind == "error" and case.provenance == "synthetic" and case.expected[0].error_class == error_class):
            lines.extend([f"### {case.id}", "", f"Error inyectado: {case.injected_errors[0].explanation}", f"Esperado estricto: `{json.dumps(asdict(case.expected[0]), ensure_ascii=False)}`", ""])
            for run in report["runs"]:
                result = run["match_results"][case.id]
                lines.extend([
                    f"#### Corrida {run['run']}",
                    f"- Strict matches: `{json.dumps(result['matches'], ensure_ascii=False)}`",
                    f"- Strict false negative: `{json.dumps(result['false_negatives'], ensure_ascii=False)}`",
                    f"- Near misses: `{json.dumps(result['near_misses'], ensure_ascii=False)}`",
                    "- Hallazgos no emparejados:",
                ])
                for finding in result["false_positives"]:
                    lines.append(f"  - id=`{finding['id']}` | severity=`{finding['severity']}` | agent=`{finding['responsible_agent']}` | category=`{finding['category']}` | artifact=`{finding['artifact_type']}:{finding['artifact_id']}`")
                    lines.append(f"    - {finding['description']}")
                lines.append("")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"evidence_extracted output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
