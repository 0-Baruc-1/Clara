"""One-off, fail-closed extractor for MINEDUC Bases Curriculares PDFs.

It intentionally keeps raw extracted wording. A candidate is only promoted to the
runtime curriculum catalog when both its wording and its subject-prefix convention
are evidenced by the source PDF. Everything else is retained in the versioned report
for manual completion from another official source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import pdfplumber
except ImportError as error:  # pragma: no cover - operator-facing setup error
    raise SystemExit("Falta pdfplumber. Instala las dependencias del backend antes de ejecutar este script.") from error


# scripts/ lives directly under backend/.
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "data" / "source" / "bases-curriculares-1-a-6-basico.pdf"
DEFAULT_CATALOG = ROOT / "app" / "curriculum" / "mineduc_objectives.json"
DEFAULT_REPORT = ROOT / "app" / "curriculum" / "mineduc_extraction_report.json"
SOURCE_NAME = "Bases Curriculares 1° a 6° Básico — Ministerio de Educación de Chile"

# OA body text sits in the right-hand column on the document pages inspected for
# this extraction. Keeping it separate prevents axis labels in the left column
# from being silently inserted into official wording.
OBJECTIVE_COLUMN_X0 = 205
OBJECTIVE_NUMBER_X0 = 190


# These are document headings, not code mappings. The command can run all of them
# and accepts --subjects to limit a first pass.
SUBJECT_PATTERNS = {
    "Artes Visuales": r"artes\s+visuales",
    "Ciencias Naturales": r"ciencias\s+naturales",
    "Educación Física y Salud": r"educaci.n\s+f.sica\s+y\s+salud",
    "Historia, Geografía y Ciencias Sociales": r"historia\s*,?\s*geograf.a\s+y\s+ciencias\s+sociales",
    "Idioma extranjero Inglés": r"idioma\s+extranjero\s+ingl.s",
    "Lenguaje y Comunicación": r"lenguaje\s+y\s+comunicaci.n",
    "Matemática": r"matem.tica",
    "Música": r"m.sica",
    "Orientación": r"orientaci.n",
    "Tecnología": r"tecnolog.a",
}
GRADE_WORDS = {
    "primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4, "quinto": 5, "sexto": 6,
}
FULL_CODE = re.compile(r"\b(?P<prefix>[A-Z]{2,6})\s*(?P<level>0?[1-6])\s+OA\s*(?P<oa>\d{1,2})\b")
OBJECTIVE_START = re.compile(r"^\s*(?P<number>\d{1,2})\s+(?P<word>[A-ZÁÉÍÓÚÜÑ])(?P<rest>.*)$")

@dataclass(frozen=True)
class ExtractedPage:
    """Raw text plus the right-side OA column, retained separately as evidence."""

    raw_text: str
    objective_lines: tuple[str, ...]


def detection_text(value: str) -> str:
    """Only for locating headings; it is never written as official wording."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def page_subject(raw_text: str) -> str | None:
    # Subject identity is a running header. Searching body text makes a page
    # about another subject steal the active context through a casual mention.
    searchable = detection_text("\n".join(raw_text.splitlines()[:4]))
    matches = [subject for subject, pattern in SUBJECT_PATTERNS.items() if re.search(pattern, searchable)]
    return matches[0] if len(matches) == 1 else None


def page_grade(raw_text: str) -> int | None:
    # The grade appears in a page header; retain the raw PDF glyphs and tolerate
    # font extraction variants only for detection (never for stored OA wording).
    header_lines = [line for line in raw_text.splitlines()[:4] if "bases curriculares" not in detection_text(line)]
    header = "\n".join(header_lines)
    numeric = re.findall(r"\b([1-6])\s*[°º]?\s*b[áa]sico\b", header, flags=re.IGNORECASE)
    searchable = detection_text(header)
    words = [GRADE_WORDS[word] for word in GRADE_WORDS if re.search(rf"\b{word}\s+b[aá]sico\b", searchable)]
    values = {int(value) for value in numeric} | set(words)
    return next(iter(values)) if len(values) == 1 else None


def extract_objective_column_lines(page: object, x0: float = OBJECTIVE_COLUMN_X0) -> tuple[str, ...]:
    """Return lines from the OA body column without rewriting their text.

    The Bases layout places axis labels in a separate left column. `extract_text`
    merges both columns in reading order, which would make an OA non-verbatim.
    This retains words beginning at the documented objective-column boundary and
    preserves PDF line boundaries in the report for manual verification.
    """
    page_text = page.extract_text() or ""  # type: ignore[attr-defined]
    # Only pages that show the `Ejes` column need the right-column crop. The
    # continuation pages use the full body width; applying the crop there would
    # silently lose OAs that begin farther left.
    cutoff = x0 if "ejes" in detection_text(page_text) else 0
    words = page.extract_words()  # type: ignore[attr-defined]
    rows: dict[float, list[dict[str, object]]] = defaultdict(list)
    for word in words:
        word_x0 = float(word["x0"])
        is_leading_number = str(word["text"]).isdigit() and word_x0 >= OBJECTIVE_NUMBER_X0
        if word_x0 >= cutoff or (cutoff and is_leading_number):
            # PDF glyphs on one visual baseline can differ by a few tenths of a
            # point (the OA number is one example). Group them as one line before
            # joining, otherwise `1` and `Reconocer ...` become separate records.
            rows[round(float(word["top"]) / 3) * 3].append(word)
    return tuple(
        " ".join(str(word["text"]) for word in sorted(row, key=lambda item: float(item["x0"])))
        for _, row in sorted(rows.items())
    )


@dataclass
class Candidate:
    subject: str | None
    grade: int | None
    oa_number: int
    wording_raw: str
    start_page: int
    end_page: int
    reasons: list[str] = field(default_factory=list)


def candidate_from_lines(subject: str | None, grade: int | None, number: int, lines: list[str], page: int) -> Candidate:
    wording = "\n".join(lines)
    reasons: list[str] = []
    if subject is None:
        reasons.append("subject_unresolved")
    if grade is None:
        reasons.append("grade_unresolved")
    if "�" in wording:
        reasons.append("text_encoding_loss")
    if any(line.rstrip().endswith("-") for line in lines[:-1]):
        reasons.append("line_wrap_hyphenation_preserved")
    return Candidate(subject, grade, number, wording, page, page, reasons)


def extract_candidates(pages: Iterable[ExtractedPage], selected_subjects: set[str]) -> tuple[list[Candidate], list[dict[str, object]]]:
    pages = list(pages)
    candidates: list[Candidate] = []
    failures: list[dict[str, object]] = []
    active_subject: str | None = None
    active_grade: int | None = None
    collecting = False
    current: Candidate | None = None

    def flush_current() -> None:
        nonlocal current
        if current is not None:
            if current.start_page != current.end_page:
                current.reasons.append("text_crosses_pages")
            if "�" in current.wording_raw and "text_encoding_loss" not in current.reasons:
                current.reasons.append("text_encoding_loss")
            if any(line.rstrip().endswith("-") for line in current.wording_raw.splitlines()[:-1]) and "line_wrap_hyphenation_preserved" not in current.reasons:
                current.reasons.append("line_wrap_hyphenation_preserved")
            wording_lines = current.wording_raw.splitlines()
            if any(
                line.rstrip().endswith((".", ":", ";"))
                and len(next_line.split()) <= 4
                for line, next_line in zip(wording_lines, wording_lines[1:])
            ):
                current.reasons.append("possible_layout_text_interleaving")
            candidates.append(current)
            current = None

    # A section header sometimes appears several pages before a numbered OA.
    # Keep this independent timeline to validate every candidate after parsing.
    subject_by_page: dict[int, str | None] = {}
    last_subject: str | None = None
    for page_number, page in enumerate(pages, start=1):
        heading_subject = page_subject(page.raw_text)
        if heading_subject is not None:
            last_subject = heading_subject
        subject_by_page[page_number] = last_subject

    for page_number, page in enumerate(pages, start=1):
        raw_text = page.raw_text
        subject = page_subject(raw_text)
        grade = page_grade(raw_text)
        context_changed = (subject and subject != active_subject) or (grade is not None and grade != active_grade)
        if context_changed:
            flush_current()
            collecting = False
        if subject:
            active_subject = subject
        if grade is not None:
            active_grade = grade
        if active_subject not in selected_subjects:
            continue

        lines = list(page.objective_lines)
        detection = detection_text(raw_text)
        if (
            ("ocisab" in detection and any(word[::-1] in detection for word in GRADE_WORDS))
            or (len(raw_text.strip()) < 80 and not re.search(r"\d", raw_text))
        ):
            flush_current()
            collecting = False
            continue
        has_oa_heading = (
            "objetivos de aprendizaje" in detection
            and "los estudiantes seran capaces" in detection
        )
        if has_oa_heading:
            collecting = True
        if not collecting:
            continue
        found_starts = 0
        for line_index, line in enumerate(lines):
            if line_index < 3 and (line.strip().isdigit() or "bases curriculares" in detection_text(line)):
                continue
            match = OBJECTIVE_START.match(line)
            if match:
                flush_current()
                current = candidate_from_lines(
                    active_subject,
                    active_grade,
                    int(match.group("number")),
                    [f"{match.group('word')}{match.group('rest')}"],
                    page_number,
                )
                found_starts += 1
            elif current is not None and not has_oa_heading:
                current.wording_raw += "\n" + line
                current.end_page = page_number
            elif current is not None and line_index > 2 and not any(
                marker in detection_text(line) for marker in ("objetivos de aprendizaje", "los estudiantes seran capaces", "ejes")
            ):
                current.wording_raw += "\n" + line
        if has_oa_heading and not found_starts:
            failures.append({"page": page_number, "reason": "oa_section_without_parseable_numbered_objectives", "subject_context": active_subject, "grade_context": active_grade, "text_excerpt": raw_text[:1200]})
    flush_current()

    validated: list[Candidate] = []
    for candidate in candidates:
        observed_subject = subject_by_page.get(candidate.start_page)
        if observed_subject == candidate.subject:
            validated.append(candidate)
            continue
        failures.append({
            "page": candidate.start_page,
            "reason": "candidate_subject_context_mismatch",
            "parsed_subject": candidate.subject,
            "observed_section_subject": observed_subject,
            "oa_number": candidate.oa_number,
            "wording_raw": candidate.wording_raw,
        })
    return validated, failures


def find_prefix_evidence(pages: Iterable[str]) -> tuple[dict[tuple[str, int], dict[str, object]], list[dict[str, object]]]:
    """Map a prefix only when a complete source code occurs on a page with one subject/grade context."""
    evidence: dict[tuple[str, int], dict[str, object]] = {}
    all_matches: list[dict[str, object]] = []
    for page_number, raw_text in enumerate(pages, start=1):
        subject, grade = page_subject(raw_text), page_grade(raw_text)
        for match in FULL_CODE.finditer(raw_text):
            item = {"page": page_number, "full_code": match.group(0), "prefix": match.group("prefix"), "level": int(match.group("level")), "oa_number": int(match.group("oa")), "subject_context": subject, "grade_context": grade}
            all_matches.append(item)
            if subject and grade is not None and grade == item["level"]:
                key = (subject, grade)
                prior = evidence.get(key)
                if prior is None:
                    evidence[key] = item
                elif prior["prefix"] != item["prefix"]:
                    evidence.pop(key, None)
    return evidence, all_matches


def build_outputs(candidates: list[Candidate], prefix_evidence: dict[tuple[str, int], dict[str, object]], requested_subjects: set[str]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    accepted: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    prefix_missing: list[dict[str, object]] = []
    seen_missing: set[tuple[str, int]] = set()

    for candidate in candidates:
        record = asdict(candidate)
        record["code_format_source"] = None
        if candidate.subject is None or candidate.grade is None:
            record["code_status"] = "unresolved"
            unresolved.append(record)
            continue
        evidence = prefix_evidence.get((candidate.subject, candidate.grade))
        if evidence is None:
            key = (candidate.subject, candidate.grade)
            if key not in seen_missing:
                prefix_missing.append({"subject": candidate.subject, "grade_level": f"{candidate.grade}° básico", "reason": "prefix_mapping_missing", "required_evidence": "Una fuente oficial que muestre el código completo (prefijo, nivel y OA)."})
                seen_missing.add(key)
            record["reasons"].append("prefix_mapping_missing")
            record["code_status"] = "prefix_mapping_missing"
            unresolved.append(record)
            continue
        if candidate.reasons:
            record["prefix_evidence"] = evidence
            record["code_format_source"] = f"PDF page {evidence['page']}"
            record["code_status"] = "wording_requires_manual_review"
            unresolved.append(record)
            continue
        prefix = str(evidence["prefix"])
        accepted.append({
            "subject": candidate.subject,
            "grade_level": f"{candidate.grade}° básico",
            "keywords": [],
            "objective": {
                "code": f"{prefix}{candidate.grade:02d} OA {candidate.oa_number}",
                "description": candidate.wording_raw,
                "source": f"{SOURCE_NAME}; formato de código verificado en p. {evidence['page']}",
            },
        })
    extracted_subjects = {candidate.subject for candidate in candidates if candidate.subject}
    for subject in sorted(requested_subjects - extracted_subjects):
        prefix_missing.append({"subject": subject, "grade_level": None, "reason": "subject_not_extracted", "required_evidence": "Revisión manual de las páginas de la asignatura."})
    return accepted, unresolved, prefix_missing


def coverage(candidates: list[Candidate], accepted: list[dict[str, object]]) -> dict[str, dict[str, dict[str, int]]]:
    result: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    for candidate in candidates:
        if candidate.subject and candidate.grade:
            result[candidate.subject][f"{candidate.grade}° básico"]["detected"] += 1
    for entry in accepted:
        result[str(entry["subject"])][str(entry["grade_level"])]["accepted"] += 1
    return {subject: {level: dict(counts) for level, counts in levels.items()} for subject, levels in result.items()}


def sequence_anomalies(candidates: list[Candidate]) -> list[dict[str, object]]:
    """Expose numbering anomalies rather than silently treating a parse as complete."""
    groups: dict[tuple[str, int], list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.subject is not None and candidate.grade is not None:
            groups[(candidate.subject, candidate.grade)].append(candidate)

    anomalies: list[dict[str, object]] = []
    for (subject, grade), entries in sorted(groups.items()):
        numbers = [entry.oa_number for entry in entries]
        counts = Counter(numbers)
        duplicates = sorted(number for number, count in counts.items() if count > 1)
        unique = sorted(counts)
        gaps = list(range(unique[0], unique[-1] + 1)) if unique else []
        missing = [number for number in gaps if number not in counts]
        if duplicates or missing:
            anomalies.append({
                "subject": subject,
                "grade_level": f"{grade}° básico",
                "detected_numbers": numbers,
                "duplicate_numbers": duplicates,
                "missing_numbers_within_detected_range": missing,
                "reason": "numbering_requires_manual_review",
            })
    return anomalies


def objective_page_evidence(candidates: list[Candidate]) -> list[dict[str, object]]:
    """Identify where the PDF showed numbered OAs, without asserting a code format."""
    groups: dict[tuple[str, int], list[int]] = defaultdict(list)
    for candidate in candidates:
        if candidate.subject is not None and candidate.grade is not None:
            groups[(candidate.subject, candidate.grade)].append(candidate.start_page)
    return [
        {
            "subject": subject,
            "grade_level": f"{grade}° básico",
            "pages_with_detected_objectives": sorted(set(pages)),
            "evidence": "Estas páginas muestran numeración de OA, no un código completo con prefijo.",
        }
        for (subject, grade), pages in sorted(groups.items())
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract MINEDUC OA verbatim and fail closed on unverified code formats.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--catalog-output", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--subjects", nargs="*", default=["Ciencias Naturales", "Matemática"])
    parser.add_argument("--all-subjects", action="store_true")
    args = parser.parse_args()
    selected = set(SUBJECT_PATTERNS if args.all_subjects else args.subjects)
    unknown = selected - set(SUBJECT_PATTERNS)
    if unknown:
        raise SystemExit(f"Asignaturas no reconocidas: {', '.join(sorted(unknown))}. Usa --all-subjects o un encabezado listado por el documento.")
    if not args.pdf.is_file():
        raise SystemExit(f"No se encontró el PDF: {args.pdf}")

    with pdfplumber.open(args.pdf) as pdf:
        pages = [
            ExtractedPage(
                raw_text=page.extract_text(x_tolerance=1, y_tolerance=3) or "",
                objective_lines=extract_objective_column_lines(page),
            )
            for page in pdf.pages
        ]
    raw_pages = [page.raw_text for page in pages]
    prefix_evidence, full_code_matches = find_prefix_evidence(raw_pages)
    candidates, parse_failures = extract_candidates(pages, selected)
    accepted, unresolved, prefix_missing = build_outputs(candidates, prefix_evidence, selected)

    catalog = {"source_name": SOURCE_NAME, "entries": accepted}
    report = {
        "schema_version": 1,
        "source_pdf": str(args.pdf),
        "source_name": SOURCE_NAME,
        "requested_subjects": sorted(selected),
        "pages_processed": len(pages),
        "wording_extraction": {
            "strategy": "Se conservaron las palabras y saltos de linea de la columna principal de OA; no se reescribio ni normalizo el texto.",
            "objective_column_x0_points": OBJECTIVE_COLUMN_X0,
            "known_limitations": [
                "Los guiones de corte de linea se conservan y se marcan para revision manual.",
                "Un OA que cruza paginas se conserva y se marca para revision manual.",
            ],
        },
        "code_format_evidence": {
            "full_code_matches": full_code_matches,
            "verified_prefix_mappings": [{"subject": subject, "grade_level": f"{grade}° básico", "evidence": item} for (subject, grade), item in sorted(prefix_evidence.items())],
            "scan_result": {
                "pages_scanned": len(pages),
                "full_code_pattern": "PREFIX+LEVEL OA NUMBER",
                "conclusion": "No se encontró un código OA completo en el texto extraíble del PDF; por eso no se infirió ningún prefijo.",
            },
            "policy": "Sin prefijo y nivel visibles en una fuente oficial, no se emite código final.",
        },
        "objective_page_evidence": objective_page_evidence(candidates),
        "coverage_by_subject_and_level": coverage(candidates, accepted),
        "numbering_anomalies": sequence_anomalies(candidates),
        "accepted_runtime_entries": len(accepted),
        "unresolved_objectives": unresolved,
        "prefix_mapping_missing": prefix_missing,
        "parse_failures": parse_failures,
        "manual_next_step": {
            "required": "Completar los prefijos solo desde una segunda fuente oficial que muestre el código OA completo.",
            "official_source_candidate": "https://www.curriculumnacional.cl/curriculum/1o-6o-basico/",
            "acceptance_rule": "Registrar la URL específica de cada OA que muestre código, asignatura, nivel y redacción oficial antes de incorporar su código al catálogo de ejecución.",
        },
    }
    args.catalog_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.catalog_output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog": str(args.catalog_output), "report": str(args.report_output), "accepted": len(accepted), "unresolved": len(unresolved), "prefix_mappings": len(prefix_evidence)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
