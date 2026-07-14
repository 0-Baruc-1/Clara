import json
from pathlib import Path
from typing import Protocol
from unicodedata import combining, normalize

from app.curriculum.models import CurriculumCatalog, CurriculumEntry


class CurriculumProvider(Protocol):
    """Seam for swapping the sample JSON for a database or full OA dataset."""

    def candidates(self, subject: str | None, grade_level: str | None) -> list[CurriculumEntry]: ...

    def cache_context(self) -> str: ...


class JsonCurriculumProvider:
    def __init__(self, path: Path | None = None) -> None:
        dataset_path = path or Path(__file__).with_name("sample_objectives.json")
        self.catalog = CurriculumCatalog.model_validate_json(dataset_path.read_text(encoding="utf-8"))

    def candidates(self, subject: str | None, grade_level: str | None) -> list[CurriculumEntry]:
        def normalized(value: str) -> str:
            decomposed = normalize("NFKD", value.casefold())
            without_marks = "".join(char for char in decomposed if not combining(char))
            return " ".join(
                without_marks.replace("°", "").replace("º", "").replace("?", "").split()
            )

        def matches(value: str | None, expected: str) -> bool:
            return not value or normalized(value) in normalized(expected)

        return [
            entry for entry in self.catalog.entries
            if matches(subject, entry.subject) and matches(grade_level, entry.grade_level)
        ]

    def cache_context(self) -> str:
        """Stable structured curriculum content, placed before request-specific data."""
        return json.dumps(self.catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
