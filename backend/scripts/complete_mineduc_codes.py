"""Complete extracted MINEDUC OAs from their individual official web pages.

This is an operator-run, one-off acquisition script. It deliberately does not
run in Clara's API process. Each accepted record has an individual public URL,
the page HTML is cached locally, and wording is compared with the accompanying
Bases Curriculares PDF extraction without silently resolving differences.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "app" / "curriculum" / "mineduc_extraction_report.json"
CATALOG_PATH = ROOT / "app" / "curriculum" / "mineduc_objectives.json"
CACHE_DIR = ROOT / "data" / "cache" / "curriculumnacional"
BASE_URL = "https://www.curriculumnacional.cl/curriculum/1o-6o-basico"
USER_AGENT = "ClaraCurriculumVerifier/1.0 (limited educational source verification)"

SUBJECTS = {
    "Ciencias Naturales": {"slug": "ciencias-naturales", "prefix": "CN"},
    "Matemática": {"slug": "matematica", "prefix": "MA"},
}
CODE_RE = re.compile(r"\b([A-Z]{2}\d{2}\s+OA\s+\d{2})\b")


class DescriptionParser(HTMLParser):
    """Extract only the official OA description field from a Drupal page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class", "") or ""
        if "field--name-description" in classes:
            self._depth = 1
            return
        if self._depth:
            if tag == "br":
                self._parts.append("\n")
                return
            self._depth += 1
            if tag in {"p", "li"}:
                self._parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._depth and tag == "br":
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._depth:
            self._depth -= 1
            if tag in {"p", "li"}:
                self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._parts.append(data)

    @property
    def wording(self) -> str:
        # This changes only document whitespace introduced by HTML indentation;
        # source words and punctuation are never generated or paraphrased.
        lines = [" ".join(line.split()) for line in "".join(self._parts).splitlines()]
        return "\n".join(line for line in lines if line).strip()


@dataclass(frozen=True)
class WebObjective:
    code: str
    description: str
    url: str
    fetched_at: str
    content_sha256: str


def normalize_for_comparison(value: str) -> str:
    """Normalize layout only, never the stored source wording."""
    lines = value.replace("\u00ad", "").splitlines()
    joined: list[str] = []
    for line in lines:
        line = line.strip()
        if joined and joined[-1].endswith("-"):
            joined[-1] = joined[-1][:-1] + line
        else:
            joined.append(line)
    value = " ".join(joined)
    value = unicodedata.normalize("NFKC", value)
    return " ".join(value.split())


def objective_url(subject: str, number: int) -> tuple[str, str]:
    details = SUBJECTS[subject]
    code = f"{details['prefix']}06 OA {number:02d}"
    slug = code.casefold().replace(" ", "-")
    return code, f"{BASE_URL}/{details['slug']}/6-basico/{slug}"


def cache_path(code: str, cache_dir: Path) -> Path:
    return cache_dir / f"{code.casefold().replace(' ', '-')}.html"


def fetch_html(url: str, target: Path, delay_seconds: float, refresh: bool) -> tuple[str, bool]:
    if target.is_file() and not refresh:
        return target.read_text(encoding="utf-8"), True
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            content = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"No fue posible consultar la ficha oficial: {error}") from error
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    time.sleep(delay_seconds)
    return content, False


def parse_web_objective(content: str, url: str, expected_code: str) -> WebObjective:
    text = html.unescape(re.sub(r"<[^>]+>", " ", content))
    codes = {" ".join(match.group(1).split()) for match in CODE_RE.finditer(text)}
    if expected_code not in codes:
        raise ValueError(f"La ficha no declara el código esperado {expected_code}.")
    parser = DescriptionParser()
    parser.feed(content)
    if not parser.wording:
        raise ValueError("La ficha no contiene una redacción de OA identificable.")
    return WebObjective(
        code=expected_code,
        description=parser.wording,
        url=url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def pdf_candidates(report: dict[str, Any], subject: str) -> dict[int, dict[str, Any]]:
    return {
        int(row["oa_number"]): row
        for row in report["unresolved_objectives"]
        if row.get("subject") == subject and row.get("grade") == 6
    }


def catalog_entry(subject: str, web: WebObjective) -> dict[str, Any]:
    return {
        "subject": subject,
        "grade_level": "6° básico",
        "keywords": [],
        "objective": {
            "code": web.code,
            "description": web.description,
            "source": web.url,
        },
    }


def complete_subject(
    report: dict[str, Any], subject: str, delay_seconds: float, refresh: bool, cache_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pdf_by_number = pdf_candidates(report, subject)
    verified_entries: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for number in sorted(pdf_by_number):
        expected_code, url = objective_url(subject, number)
        try:
            content, from_cache = fetch_html(url, cache_path(expected_code, cache_dir), delay_seconds, refresh)
            web = parse_web_objective(content, url, expected_code)
        except (RuntimeError, ValueError) as error:
            failures.append({"subject": subject, "oa_number": number, "expected_code": expected_code, "url": url, "reason": str(error)})
            continue

        pdf = pdf_by_number[number]
        wording_match = normalize_for_comparison(pdf["wording_raw"]) == normalize_for_comparison(web.description)
        comparisons.append({
            "subject": subject,
            "grade_level": "6° básico",
            "oa_number": number,
            "code": web.code,
            "official_url": web.url,
            "website_wording": web.description,
            "pdf_pages": [pdf["start_page"], pdf["end_page"]],
            "pdf_wording": pdf["wording_raw"],
            "wording_match_after_layout_normalization": wording_match,
            "comparison_status": "match" if wording_match else "divergence_requires_manual_review",
            "fetched_at": web.fetched_at,
            "cache": {"path": cache_path(expected_code, cache_dir).relative_to(ROOT).as_posix(), "reused": from_cache, "content_sha256": web.content_sha256},
        })
        # The PDF itself still lacks a prefix convention. This separate source
        # makes the code usable, while retaining the PDF limitation and any
        # wording divergence for audit rather than overwriting either source.
        pdf["code_status"] = "verified_from_curriculumnacional_cl"
        pdf["code_format_source"] = web.url
        pdf["web_verification"] = {
            "code": web.code,
            "official_url": web.url,
            "official_wording": web.description,
            "wording_match_after_layout_normalization": wording_match,
        }
        verified_entries.append(catalog_entry(subject, web))
    return verified_entries, comparisons, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Complete verified OA codes from individual Currículum Nacional pages.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--subjects", nargs="*", default=["Ciencias Naturales", "Matemática"])
    parser.add_argument("--delay-seconds", type=float, default=1.25)
    parser.add_argument("--refresh", action="store_true", help="Reconsulta fichas ya presentes en caché.")
    args = parser.parse_args()
    if args.delay_seconds < 1:
        raise SystemExit("Usa al menos un segundo entre solicitudes nuevas para no sobrecargar el sitio.")
    unknown = set(args.subjects) - set(SUBJECTS)
    if unknown:
        raise SystemExit(f"Asignaturas no configuradas para esta pasada: {', '.join(sorted(unknown))}")

    report = json.loads(args.report.read_text(encoding="utf-8"))
    all_entries: list[dict[str, Any]] = []
    all_comparisons: list[dict[str, Any]] = []
    all_failures: list[dict[str, Any]] = []
    for subject in args.subjects:
        entries, comparisons, failures = complete_subject(report, subject, args.delay_seconds, args.refresh, args.cache_dir)
        all_entries.extend(entries)
        all_comparisons.extend(comparisons)
        all_failures.extend(failures)

    catalog = {
        "source_name": "Currículum Nacional de Chile — fichas oficiales de OA verificadas individualmente",
        "entries": all_entries,
    }
    report["web_completion"] = {
        "status": "complete" if not all_failures else "partial",
        "scope": {"subjects": args.subjects, "grade_level": "6° básico"},
        "source_index_urls": {
            "Ciencias Naturales": f"{BASE_URL}/ciencias-naturales/6-basico",
            "Matemática": f"{BASE_URL}/matematica/6-basico",
        },
        "acquisition_policy": {
            "individual_page_required": True,
            "request_delay_seconds": args.delay_seconds,
            "local_cache": str(args.cache_dir.relative_to(ROOT)),
            "refresh_requires_explicit_flag": True,
            "robots_checked": "https://www.curriculumnacional.cl/robots.txt",
            "robots_result": "Las rutas /curriculum/ no están desautorizadas para User-agent: *.",
            "structured_export_check": "No se encontró sitemap.xml ni sitemap_index.xml; se usaron los listados oficiales por curso y asignatura como índice.",
            "site_access_statement": "El sitio declara que deja la información curricular oficial disponible para toda la ciudadanía y permite visualizar y descargar sus Bases Curriculares.",
            "terms_of_use_check": "No se encontró una página pública de términos de uso ni una prohibición explícita de consulta automatizada; por eso la adquisición quedó limitada, identificada, rate-limited y cacheada.",
        },
        "verified_objectives": len(all_entries),
        "failed_objectives": all_failures,
        "pdf_website_comparisons": all_comparisons,
        "contribution_by_source": {
            "bases_pdf": "asignatura, nivel, número OA, texto extraído y páginas de evidencia",
            "curriculumnacional_cl": "código OA, redacción oficial, URL de evidencia individual y hash del HTML cacheado",
        },
    }
    args.catalog.parent.mkdir(parents=True, exist_ok=True)
    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog": str(args.catalog), "report": str(args.report), "verified": len(all_entries), "failed": len(all_failures), "divergences": sum(not row["wording_match_after_layout_normalization"] for row in all_comparisons)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
